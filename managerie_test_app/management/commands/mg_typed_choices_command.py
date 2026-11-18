import json

from django.core.management import BaseCommand
from django.core.management.base import CommandParser


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--level", type=int, choices=[1, 2, 3], default=2)

    def handle(self, **options):
        # These comparisons would crash if the values arrived as strings.
        if options["verbosity"] >= 1 and options["level"] >= 1:
            data = {key: [options[key], type(options[key]).__name__] for key in ("verbosity", "level")}
            self.stdout.write("XXX:" + json.dumps(data, sort_keys=True) + ":XXX")
