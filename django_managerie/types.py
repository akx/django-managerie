from collections.abc import Mapping

from django_managerie.commands import ManagementCommand

CommandMap = Mapping[str, ManagementCommand]
