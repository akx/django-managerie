# -- encoding: UTF-8 --
import warnings
from argparse import _HelpAction, _StoreAction, _StoreTrueAction, _StoreFalseAction, _StoreConstAction

from django import forms

FIELD_CLASS_MAP = {
    float: forms.FloatField,
    int: forms.IntegerField,
    None: forms.CharField,
}


class ArgumentParserForm(forms.Form):

    IGNORED_DESTS = {
        'pythonpath',
        'settings',
        'no_color',
        'traceback',
    }

    def __init__(self, *, parser, **kwargs):
        """
        :type parser: argparse.ArgumentParser
        """
        self.parser = parser
        super(ArgumentParserForm, self).__init__(**kwargs)
        for action in self.parser._actions:
            if isinstance(action, _HelpAction):
                continue
            if action.dest in self.IGNORED_DESTS:
                continue
            field_cls = None
            field_kwargs = dict(
                initial=action.default,
                label=action.dest.replace('_', ' ').title(),
                help_text=action.help,
                required=action.required,
            )
            if isinstance(action, (_StoreTrueAction, _StoreFalseAction, _StoreConstAction)):
                field_cls = forms.BooleanField
            elif isinstance(action, _StoreAction):
                if action.type not in FIELD_CLASS_MAP:
                    warnings.warn('No specific field class for type %r' % action.type)
                field_cls = FIELD_CLASS_MAP.get(action.type, forms.Field)
            if field_cls:
                self.fields[action.dest] = field_cls(**field_kwargs)

            # TODO: Probably support for more fields :)
