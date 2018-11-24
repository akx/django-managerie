import json

from django.core.management import BaseCommand


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--true-option', action='store_true', dest='foo')
        parser.add_argument('--false-option', action='store_false', dest='bar')
        parser.add_argument('string_option', default='wololo')

    def handle(self, **options):
        data = json.dumps(options, default=str, sort_keys=True)
        self.stdout.write('XXX:' + data + ':XXX')
