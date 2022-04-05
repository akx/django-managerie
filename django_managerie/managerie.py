from typing import Any, Callable, Dict, List, Tuple

import wrapt
from django.apps.config import AppConfig
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.decorators import user_passes_test
from django.urls import URLPattern, path, reverse

from django_managerie.blocklist import COMMAND_BLOCKLIST
from django_managerie.commands import ManagementCommand, get_commands
from django_managerie.types import CommandMap
from django_managerie.views import ManagerieCommandView, ManagerieListView

superuser_required = user_passes_test(lambda u: u.is_active and u.is_superuser)


class Managerie:
    ignored_app_names = {
        'django.core',
        'django.contrib.staticfiles',
    }

    def __init__(self, admin_site: AdminSite) -> None:
        self.admin_site = admin_site

    def patch(self) -> None:
        if hasattr(self.admin_site, 'patched_by_managerie'):
            return
        old_get_app_list = self.admin_site.get_app_list
        self.admin_site.get_app_list = self.patched_get_app_list(old_get_app_list)  # type: ignore[assignment]
        old_get_urls = self.admin_site.get_urls
        self.admin_site.get_urls = self.patched_get_urls(old_get_urls)  # type: ignore[assignment]
        self.admin_site.patched_by_managerie = True  # type: ignore[attr-defined]

    def is_command_allowed(self, command: ManagementCommand) -> bool:
        # This could be overridden in a subclass to allow for more fine-grained
        # control over which commands are allowed.

        if command.full_name in COMMAND_BLOCKLIST:
            return False
        if getattr(command.get_command_class(), 'disable_managerie', False):
            return False
        return True

    def get_commands(self) -> Dict[AppConfig, CommandMap]:
        command_map: Dict[AppConfig, CommandMap] = {}
        for app_config, commands in get_commands().items():
            command_map[app_config] = {
                command_name: command
                for (command_name, command)
                in commands.items()
                if self.is_command_allowed(command)
            }
        return command_map

    def get_commands_for_app_label(self, app_label: str) -> CommandMap:
        for app_config, commands in self.get_commands().items():
            if app_config.label == app_label:
                return commands
        return {}

    @wrapt.decorator
    def patched_get_app_list(self, wrapped, instance: AdminSite, args, kwargs):
        request = args[0]
        app_list = wrapped(*args, **kwargs)
        if request.user.is_superuser:
            self._augment_app_list(app_list)
        return app_list

    @wrapt.decorator
    def patched_get_urls(self, wrapped: Callable, instance: AdminSite, args: Tuple[()], kwargs: Dict[Any, Any]) -> list:
        urls = wrapped(*args, **kwargs)
        return self._get_urls() + list(urls)

    def _augment_app_list(self, app_list):
        all_commands = {app_config.label: commands for (app_config, commands) in self.get_commands().items()}
        for app in app_list:
            commands = all_commands.get(app['app_label'], [])
            if commands:
                app.setdefault('models', []).append({
                    'perms': {'change': True},
                    'admin_url': reverse(
                        'admin:managerie_list',
                        kwargs={'app_label': app['app_label']},
                        current_app=self.admin_site.name,
                    ),
                    'name': 'Commands',
                    'object_name': '_ManagerieCommands_',
                })

    def _get_urls(self) -> List[URLPattern]:
        return [
            path(
                'managerie/<app_label>/<command>/',
                superuser_required(ManagerieCommandView.as_view(managerie=self)),
                name='managerie_command',
            ),
            path(
                'managerie/<app_label>/',
                superuser_required(ManagerieListView.as_view(managerie=self)),
                name='managerie_list',
            ),
            path(
                'managerie/',
                superuser_required(ManagerieListView.as_view(managerie=self)),
                name='managerie_list_all',
            ),
        ]

    @property
    def urls(self):
        return (self._get_urls(), 'admin', self.admin_site.name)
