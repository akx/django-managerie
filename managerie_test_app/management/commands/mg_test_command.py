import json

from django.core.management import BaseCommand
from django.core.management.base import CommandParser


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--true-option', action='store_true', dest='foo')
        parser.add_argument('--false-option', action='store_false', dest='bar')
        parser.add_argument('string_option', default='wololo')

    def handle(self, **options):
        request = getattr(self, '_managerie_request', None)
        data = json.dumps({
            **options,
            'username': request.user.username,
        }, default=str, sort_keys=True)
        self.stdout.write('XXX:' + data + ':XXX')
