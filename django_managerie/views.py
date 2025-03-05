import io
import sys
import time
import traceback
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from itertools import chain
from typing import Any, BinaryIO, Dict, Iterable, Optional

from django import forms
from django.apps import apps
from django.apps.config import AppConfig
from django.contrib.auth.mixins import AccessMixin
from django.http import Http404, HttpResponse
from django.views.generic import FormView, TemplateView

from django_managerie.commands import ManagementCommand
from django_managerie.forms import ArgumentParserForm
from django_managerie.managerie import Managerie


@contextmanager
def redirect_stdin_binary(input_bin_stream: BinaryIO):
    old_stdin = sys.stdin
    try:
        sys.stdin = io.TextIOWrapper(input_bin_stream, encoding="UTF-8")
        assert sys.stdin.buffer is input_bin_stream
        yield
    finally:
        sys.stdin = old_stdin


class ManagerieBaseMixin:
    managerie: Optional[Managerie] = None
    kwargs: Dict[str, Any]
    _app: Optional[AppConfig]

    def get_app(self) -> Optional[AppConfig]:
        if hasattr(self, "_app"):
            return self._app
        if "app_label" in self.kwargs:
            self._app = apps.get_app_config(self.kwargs["app_label"])
            return self._app
        return None


class StaffRequiredMixin(AccessMixin):
    """
    Verify that the current user is authenticated and is a staff member.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.is_staff:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class ManagerieListView(ManagerieBaseMixin, StaffRequiredMixin, TemplateView):
    template_name = "django_managerie/admin/list.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["app"] = app = self.get_app()
        context["title"] = f"{app.verbose_name if app else 'All Apps'} – Commands"
        managerie = self.managerie
        assert managerie
        commands: Iterable[ManagementCommand]
        if app:
            commands = managerie.get_commands_for_app_label(
                request=self.request,
                app_label=app.label,
            ).values()
        else:
            commands = chain(
                *(app_commands.values() for app_commands in managerie.get_commands(request=self.request).values()),
            )
        context["commands"] = sorted(commands, key=lambda cmd: cmd.full_title)
        return context


class ManagerieCommandView(ManagerieBaseMixin, StaffRequiredMixin, FormView):
    template_name = "django_managerie/admin/command.html"

    @property
    def command_name(self) -> str:
        return self.kwargs["command"]

    def get_command_object(self) -> ManagementCommand:
        app = self.get_app()
        managerie = self.managerie
        assert app and managerie
        try:
            return managerie.get_commands_for_app_label(
                request=self.request,
                app_label=app.label,
            )[self.command_name]
        except KeyError:
            raise Http404(
                f"Command {self.command_name} not found in {app.label} (or you don't have permission to run it)",
            )

    def get_form(self, form_class=None) -> ArgumentParserForm:
        cmd = self.get_command_object().get_command_instance()
        parser = cmd.create_parser("django", self.command_name)
        form = ArgumentParserForm(parser=parser, **self.get_form_kwargs())
        if getattr(cmd, "managerie_accepts_stdin", False):
            form.fields["_managerie_stdin_file"] = forms.FileField(
                label="Input file",
                required=False,
            )
            form.fields["_managerie_stdin_content"] = forms.CharField(
                label="Input text",
                widget=forms.Textarea,
                help_text="Used only if input file is not set",
                required=False,
            )
        return form

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        command = self.get_command_object()
        context.update(
            app=self.get_app(),
            command=command,
            command_help=command.get_command_instance().help,
            title=command.full_title,
        )
        return context

    def form_valid(self, form: ArgumentParserForm) -> HttpResponse:
        # This mimics BaseCommand.run_from_argv():
        options = dict(form.cleaned_data)
        # "Move positional args out of options to mimic legacy optparse"
        args = options.pop("args", ())

        # Handle input
        if stdin_file := form.cleaned_data.pop("_managerie_stdin_file", None):
            stdin_binary = stdin_file.file
        elif stdin_content := form.cleaned_data.pop("_managerie_stdin_content", None):
            stdin_binary = io.BytesIO(stdin_content.encode("UTF-8"))
        else:
            stdin_binary = io.BytesIO()

        stdout = io.StringIO()
        stderr = io.StringIO()
        error = None
        error_tb = None
        t0 = time.time()
        co = self.get_command_object()
        with redirect_stdin_binary(stdin_binary), redirect_stdout(stdout), redirect_stderr(stderr):
            options.update(
                {
                    "traceback": True,
                    "no_color": True,
                    "force_color": False,
                    "stdout": stdout,
                    "stderr": stderr,
                },
            )
            cmd = co.get_command_instance()
            try:
                cmd._managerie_request = self.request
                cmd.execute(*args, **options)
            except SystemExit as se:  # We don't want any stray sys.exit()s to quit the app server
                stderr.write(f"<exit: {se}>")
            except Exception as exc:
                error = exc
                error_tb = traceback.format_exc()
        context = self.get_context_data(
            executed=True,
            form=form,
            error=error,
            error_tb=error_tb,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
            duration=(time.time() - t0),
        )
        return self.render_to_response(context=context, status=(400 if error else 200))
