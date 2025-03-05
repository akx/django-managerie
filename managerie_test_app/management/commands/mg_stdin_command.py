import sys

from django.core.management import BaseCommand
from django.core.management.base import CommandParser


class Command(BaseCommand):
    managerie_accepts_stdin = True

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--operation", choices=["uppercase", "reverse", "count FF bytes"], required=True)

    def handle(self, operation, **options):
        if operation == "uppercase":
            content = sys.stdin.read().upper()
        elif operation == "reverse":
            content = sys.stdin.read()[::-1]
        elif operation == "count FF bytes":
            n = sys.stdin.buffer.read().count(b"\xff")
            content = f"Found {n} FF bytes"
        self.stdout.write(content)
