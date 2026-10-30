"""Which models expose a chatter, and who may read or write it.

Each Django app declares its records in a ``chatter.py`` module, the way
``admin.py`` works. These modules are imported when the app registry is ready::

    # crm/chatter.py
    from chatter import register
    from crm.models import Lead
    from crm.permissions import IsSales

    register(Lead, permission_classes=[IsSales])
"""

from dataclasses import dataclass

from django.core.exceptions import ImproperlyConfigured

_registry = {}


@dataclass(frozen=True)
class Entry:
    model: type
    permission_classes: tuple


def register(model, name=None, permission_classes=()):
    """Expose `model` at ``<name>/<pk>/``. `name` defaults to the lowercase model name.

    Authenticated users always pass; `permission_classes` narrow that further and
    should be the classes that guard the record's own API.
    """
    name = name or model._meta.model_name
    if name in _registry and _registry[name].model is not model:
        raise ImproperlyConfigured(f"Chatter name {name!r} is already used by {_registry[name].model.__name__}.")
    _registry[name] = Entry(model, tuple(permission_classes))
    return model


def get_entry(name):
    return _registry.get(name)
