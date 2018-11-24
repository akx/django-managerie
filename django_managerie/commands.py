# -- encoding: UTF-8 --
import os
from collections import defaultdict, OrderedDict
from importlib import import_module

from django.apps import apps
from django.core.management import find_commands
from django.urls import reverse
from django.utils import lru_cache

from django_managerie.blacklist import BLACKLIST


class ManagementCommand:
    def __init__(self, app_config, name):
        self.app_config = app_config
        self.name = name
        self.title = self.name.replace('_', ' ').title()

    @property
    def url(self):
        return reverse(
            'admin:managerie_command',
            kwargs={'app_label': self.app_config.label, 'command': self.name},
        )

    def get_command_class(self):
        mname = '%s.management.commands.%s' % (self.app_config.name, self.name)
        return import_module(mname).Command

    def get_command_instance(self):
        cls = self.get_command_class()
        return cls()

    @property
    def is_enabled(self):
        if self.full_name in BLACKLIST:
            return False
        if getattr(self.get_command_class(), 'disable_managerie', False):
            return False
        return True

    @property
    def full_title(self):
        return '%s \u2013 %s' % (self.app_config.verbose_name, self.title)

    @property
    def full_name(self):
        return '%s.%s' % (self.app_config.label, self.name)


@lru_cache.lru_cache(maxsize=None)
def get_commands():
    # Logic filched from django.core.management.get_commands(), but expressed in a saner way.
    apps_to_commands = defaultdict(OrderedDict)

    for app_config in apps.get_app_configs():
        path = os.path.join(app_config.path, 'management')
        for command_name in find_commands(path):
            cmd = ManagementCommand(
                app_config=app_config,
                name=command_name,
            )
            if not cmd.is_enabled:
                continue
            apps_to_commands[app_config][command_name] = cmd
    return apps_to_commands
