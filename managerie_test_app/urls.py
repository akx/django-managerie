from django.contrib import admin
from django.http import HttpRequest
from django.urls import path

from django_managerie import Managerie
from django_managerie.commands import ManagementCommand


class CustomManagerie(Managerie):
    def is_command_allowed(
        self, request: HttpRequest, command: ManagementCommand
    ) -> bool:
        if command.full_name == 'managerie_test_app.mg_unprivileged_command':
            return bool(getattr(request.user, "is_staff", False))
        return super().is_command_allowed(request, command)


m = CustomManagerie(admin.site)
m.patch()

urlpatterns = [
    path('admin/', admin.site.urls),
]
