import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "managerie_tests.settings")


def manage():
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    manage()
