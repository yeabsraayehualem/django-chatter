# django-record-chatter

Odoo-style chatter for any Django model: a per-record timeline of internal notes,
system events and field changes, with who did what. Works with any user model and
any primary key type (integer, UUID, string).

## Install

```bash
pip install django-record-chatter
```

```python
# settings.py
INSTALLED_APPS = [
    ...,
    "django.contrib.contenttypes",
    "rest_framework",
    "chatter",
]

# urls.py
path("api/chatter/", include("chatter.urls")),
```

Then run `python manage.py migrate`.

## Expose a model

Add a `chatter.py` module to the app, like `admin.py`. It is picked up automatically.

```python
# crm/chatter.py
from chatter import register
from crm.models import Lead
from crm.permissions import IsSales

register(Lead, permission_classes=[IsSales])
register(Invoice, name="invoice")  # name defaults to the lowercase model name
```

| Request | Result |
| --- | --- |
| `GET api/chatter/lead/42/` | The record's messages, newest first |
| `POST api/chatter/lead/42/` with `{"body": "..."}` | Logs a note |

Requests must be authenticated. Pass the permission classes that guard the record's
own API: `has_permission` and `has_object_permission` are both checked. A model
registered without any is readable and writable by every authenticated user. Models
that are not registered return 404.

## Track changes

```python
from chatter.tracking import log_changes, post_message, snapshot

TRACKED_FIELDS = ["status", "assignee", "tags"]

def perform_update(self, serializer):
    before = snapshot(serializer.instance, TRACKED_FIELDS)
    lead = serializer.save()
    log_changes(lead, before, TRACKED_FIELDS, self.request.user)

post_message(lead, body="Lead created.", author=self.request.user)
```

- `log_changes` writes nothing when no tracked field changed, and returns the message
  or `None`.
- `labels={"status": "Stage"}` overrides the field label.
- `record=parent` logs a child object's changes on its parent's chatter.
- Choice, foreign key, many-to-many and date fields are stored as readable text.

`chatter.tracking.messages_for(record)` returns a record's messages as a queryset.

## Good to know

- Messages use a generic foreign key, so they stay in place when the record is deleted.
- `object_id` is a string, so a `GenericRelation` to `Message` cannot join on integer
  primary keys in PostgreSQL. Use `messages_for` instead.

## Tests

```bash
pip install -e .
python -m django test tests --settings=tests.settings
```
