import io
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from itertools import chain
from typing import TYPE_CHECKING, Any, Dict, Optional

from django.apps import apps
from django.apps.config import AppConfig
from django.http import Http404, HttpResponse
from django.views.generic import FormView, TemplateView

from django_managerie.commands import ManagementCommand
from django_managerie.forms import ArgumentParserForm

if TYPE_CHECKING:
    from django_managerie.managerie import Managerie


class MenagerieBaseMixin:
    managerie: Optional["Managerie"] = None
    kwargs: Dict[str, Any]
    _app: Optional[AppConfig]

    def get_app(self) -> Optional[AppConfig]:
        if hasattr(self, '_app'):
            return self._app
        if 'app_label' in self.kwargs:
            self._app = apps.get_app_config(self.kwargs['app_label'])
            return self._app
        return None


class ManagerieListView(MenagerieBaseMixin, TemplateView):
    template_name = 'django_managerie/admin/list.html'

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['app'] = app = self.get_app()
        context['title'] = f"{app.verbose_name if app else 'All Apps'} – Commands"
        managerie = self.managerie
        assert managerie
        context['commands'] = sorted(
            (
                managerie.get_commands_for_app_label(app.label).values()
                if app
                else chain(*(app_commands.values() for app_commands in managerie.get_commands().values()))
            ),
            key=lambda cmd: cmd.full_title
        )
        return context


class ManagerieCommandView(MenagerieBaseMixin, FormView):
    template_name = 'django_managerie/admin/command.html'

    @property
    def command_name(self) -> str:
        return self.kwargs['command']

    def get_command_object(self) -> ManagementCommand:
        app = self.get_app()
        managerie = self.managerie
        assert app and managerie
        try:
            return managerie.get_commands_for_app_label(app.label)[self.command_name]
        except KeyError:
            raise Http404(f"Command {self.command_name} not found in {app.label}")

    def get_form(self, form_class=None) -> ArgumentParserForm:
        cmd = self.get_command_object().get_command_instance()
        parser = cmd.create_parser('django', self.command_name)
        return ArgumentParserForm(parser=parser, **self.get_form_kwargs())

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
        args = options.pop('args', ())  # "Move positional args out of options to mimic legacy optparse"
        stdout = io.StringIO()
        stderr = io.StringIO()
        error = None
        error_tb = None
        t0 = time.time()
        co = self.get_command_object()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            options.update({
                'traceback': True,
                'no_color': True,
                'force_color': False,
                'stdout': stdout,
                'stderr': stderr,
            })
            cmd = co.get_command_instance()
            try:
                cmd.execute(*args, **options)
            except SystemExit as se:  # We don't want any stray sys.exit()s to quit the app server
                stderr.write(f'<exit: {se}>')
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
