from functools import wraps
from typing import Dict, List

from django.apps.config import AppConfig
from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest
from django.urls import URLPattern, path, reverse

from django_managerie.blocklist import COMMAND_BLOCKLIST
from django_managerie.commands import ManagementCommand, get_commands
from django_managerie.types import CommandMap


def user_is_superuser(request: HttpRequest) -> bool:
    """
    Return True if the user is an active superuser, False otherwise.
    """
    return bool(request.user.is_active and getattr(request.user, "is_superuser", None))


class Managerie:
    ignored_app_names = {
        "django.core",
        "django.contrib.staticfiles",
    }

    def __init__(self, admin_site: AdminSite) -> None:
        self.admin_site = admin_site

    def patch(self) -> None:
        if hasattr(self.admin_site, "patched_by_managerie"):
            return
        old_get_app_list = self.admin_site.get_app_list
        old_get_urls = self.admin_site.get_urls

        @wraps(old_get_app_list)
        def patched_get_app_list(request: HttpRequest, *args, **kwargs):
            app_list = old_get_app_list(request, *args, **kwargs)
            if user_is_superuser(request):
                self._augment_app_list(request, app_list)
            return app_list

        @wraps(old_get_urls)
        def patched_get_urls() -> list:
            return self._get_urls() + list(old_get_urls())

        self.admin_site.get_app_list = patched_get_app_list  # type: ignore[assignment]
        self.admin_site.get_urls = patched_get_urls  # type: ignore[assignment]
        self.admin_site.patched_by_managerie = True  # type: ignore[attr-defined]

    def is_command_allowed(
        self,
        request: HttpRequest,
        command: ManagementCommand,
    ) -> bool:
        """
        Return True if the command is allowed to be run in the current request.

        The default implementation checks if the command is enabled and then
        whether the user is a superuser.

        This can be overridden to implement per-command permissions.
        """
        if not self.is_command_enabled(command):
            return False
        return user_is_superuser(request)

    def is_command_enabled(self, command: ManagementCommand) -> bool:
        """
        Return True if the command is enabled (not blocklisted or opt-outed).

        This is only called by `is_command_allowed` as a pre-check before
        checking for per-request permissions.
        """
        if command.full_name in COMMAND_BLOCKLIST:
            return False
        if getattr(command.get_command_class(), "disable_managerie", False):
            return False
        return True

    def get_commands(
        self,
        request: HttpRequest,
    ) -> Dict[AppConfig, CommandMap]:
        command_map: Dict[AppConfig, CommandMap] = {}
        for app_config, commands in get_commands().items():
            command_map[app_config] = {
                command_name: command
                for (command_name, command) in commands.items()
                if self.is_command_allowed(command=command, request=request)
            }
        return command_map

    def get_commands_for_app_label(
        self,
        request: HttpRequest,
        app_label: str,
    ) -> CommandMap:
        for app_config, commands in self.get_commands(request).items():
            if app_config.label == app_label:
                return commands
        return {}

    def _augment_app_list(
        self,
        request: HttpRequest,
        app_list: List[Dict],
    ):
        # TODO: apps without models won't have their commands shown here since they
        #       don't show up in the app_list. We should probably show them anyway.
        all_commands: Dict[str, CommandMap] = {
            app_config.label: commands for (app_config, commands) in self.get_commands(request).items()
        }
        for app in app_list:
            if all_commands.get(app["app_label"]):  # Has commands?
                app.setdefault("models", []).append(self._make_app_command(app))

    def _make_app_command(self, app):
        return {
            "perms": {"change": True},
            "admin_url": reverse(
                "admin:managerie_list",
                kwargs={"app_label": app["app_label"]},
                current_app=self.admin_site.name,
            ),
            "name": "Commands",
            "object_name": "_ManagerieCommands_",
        }

    def _get_urls(self) -> List[URLPattern]:
        from django_managerie.views import ManagerieCommandView, ManagerieListView

        return [
            path(
                "managerie/<app_label>/<command>/",
                ManagerieCommandView.as_view(managerie=self),
                name="managerie_command",
            ),
            path(
                "managerie/<app_label>/",
                ManagerieListView.as_view(managerie=self),
                name="managerie_list",
            ),
            path(
                "managerie/",
                ManagerieListView.as_view(managerie=self),
                name="managerie_list_all",
            ),
        ]

    @property
    def urls(self):
        return (self._get_urls(), "admin", self.admin_site.name)
