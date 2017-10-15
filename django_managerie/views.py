import io
import traceback

import time
from itertools import chain

from django.apps import apps
from django.views.generic import TemplateView, FormView

from django_managerie.forms import ArgumentParserForm
from .compat import redirect_stdout, redirect_stderr


class MenagerieBaseMixin:
    managerie = None

    def get_app(self):
        if hasattr(self, '_app'):
            return self._app
        if 'app_label' in self.kwargs:
            self._app = apps.get_app_config(self.kwargs['app_label'])
            return self._app


class ManagerieListView(MenagerieBaseMixin, TemplateView):
    template_name = 'django_managerie/admin/list.html'

    def get_context_data(self, **kwargs):
        context = super(ManagerieListView, self).get_context_data(**kwargs)
        context['app'] = app = self.get_app()
        context['title'] = '%s \u2013 Commands' % (app.verbose_name if app else 'All Apps')
        context['commands'] = sorted(
            (
                self.managerie.get_commands_for_app_label(app.label).values()
                if app
                else chain(*(app_commands.values() for app_commands in self.managerie.get_commands().values()))
            ),
            key=lambda cmd: cmd.full_title
        )
        return context


class ManagerieCommandView(MenagerieBaseMixin, FormView):
    template_name = 'django_managerie/admin/command.html'

    def get_command_object(self):
        return self.managerie.get_commands_for_app_label(self.get_app().label)[self.kwargs['command']]

    def get_form(self, form_class=None):
        cmd = self.get_command_object().get_command_instance()
        parser = cmd.create_parser('django', self.kwargs['command'])
        return ArgumentParserForm(parser=parser, **self.get_form_kwargs())

    def get_context_data(self, **kwargs):
        context = super(ManagerieCommandView, self).get_context_data(**kwargs)
        context['app'] = self.get_app()
        context['command'] = cmd = self.get_command_object()
        context['command_help'] = cmd.get_command_instance().help
        context['title'] = cmd.full_title
        return context

    def form_valid(self, form):
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
                'stdout': stdout,
                'stderr': stderr,
            })
            cmd = co.get_command_instance()
            try:
                cmd.execute(*args, **options)
            except SystemExit as se:  # We don't want any stray sys.exit()s to quit the app server
                stderr.write('<exit: %s>' % se)
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
