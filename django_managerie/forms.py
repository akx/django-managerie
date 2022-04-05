import argparse
import warnings
from typing import Any, Mapping, Optional, Type

from django import forms

BOOLEAN_ACTIONS = (argparse._StoreTrueAction, argparse._StoreFalseAction, argparse._StoreConstAction)

FIELD_CLASS_MAP: Mapping[Any, Type[forms.Field]] = {
    float: forms.FloatField,
    int: forms.IntegerField,
    None: forms.CharField,
}


class ArgumentParserForm(forms.Form):
    IGNORED_DESTS = {
        'force_color',
        'no_color',
        'pythonpath',
        'settings',
        'traceback',
    }

    def __init__(self, *, parser: argparse.ArgumentParser, **kwargs) -> None:
        super().__init__(**kwargs)
        self.parser = parser
        for action in self.parser._actions:
            self._process_action(action)

    def _process_action(self, action: argparse.Action) -> None:
        if isinstance(action, argparse._HelpAction):
            return
        if action.dest in self.IGNORED_DESTS:
            return
        field_cls: Optional[Type[forms.Field]] = None
        field_kwargs = dict(
            initial=action.default,
            label=action.dest.replace('_', ' ').title(),
            help_text=action.help,
            required=action.required,
        )
        if isinstance(action, BOOLEAN_ACTIONS):
            field_cls = forms.BooleanField
        elif isinstance(action, argparse._StoreAction):
            if action.type not in FIELD_CLASS_MAP:
                warnings.warn(f'No specific field class for type {action.type!r}')
            field_cls = FIELD_CLASS_MAP.get(action.type, forms.Field)
        if field_cls:
            self.fields[action.dest] = field_cls(**field_kwargs)

        # TODO: Probably support for more fields :)
