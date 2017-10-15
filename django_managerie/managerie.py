# -- encoding: UTF-8 --

import wrapt
from django.conf.urls import url
from django.contrib.auth.decorators import user_passes_test
from django.urls import reverse

from django_managerie.commands import get_commands
from django_managerie.views import ManagerieCommandView, ManagerieListView

superuser_required = user_passes_test(lambda u: u.is_active and u.is_superuser)


class Managerie:
    ignored_app_names = {
        'django.core',
        'django.contrib.staticfiles',
    }

    def __init__(self, admin_site):
        self.admin_site = admin_site

    def patch(self):
        if hasattr(self.admin_site, 'patched_by_managerie'):
            return
        self.admin_site.get_app_list = self.patched_get_app_list(self.admin_site.get_app_list)
        self.admin_site.get_urls = self.patched_get_urls(self.admin_site.get_urls)
        self.admin_site.patched_by_managerie = True

    def get_commands(self):
        return {
            app_config: commands
            for (app_config, commands)
            in get_commands().items()
            if app_config.name not in self.ignored_app_names
        }

    def get_commands_for_app_label(self, app_label):
        for app_config, commands in self.get_commands().items():
            if app_config.label == app_label:
                return commands
        return []

    @wrapt.decorator
    def patched_get_app_list(self, wrapped, instance, args, kwargs):
        request = args[0]
        app_list = wrapped(*args, **kwargs)
        if request.user.is_superuser:
            self._augment_app_list(app_list)
        return app_list

    @wrapt.decorator
    def patched_get_urls(self, wrapped, instance, args, kwargs):
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

    def _get_urls(self):
        return [
            url(
                '^managerie/(?P<app_label>.+?)/(?P<command>.+?)/$',
                superuser_required(ManagerieCommandView.as_view(managerie=self)),
                name='managerie_command',
            ),
            url(
                '^managerie/(?P<app_label>.+?)/$',
                superuser_required(ManagerieListView.as_view(managerie=self)),
                name='managerie_list',
            ),
            url(
                '^managerie/$',
                superuser_required(ManagerieListView.as_view(managerie=self)),
                name='managerie_list_all',
            ),
        ]

    @property
    def urls(self):
        return (self._get_urls(), 'admin', self.admin_site.name)
