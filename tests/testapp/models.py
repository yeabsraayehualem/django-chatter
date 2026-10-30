import uuid

from django.conf import settings
from django.db import models


class Ticket(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        DONE = "done", "Done"

    title = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    watchers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="+")


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=100)


class Secret(models.Model):
    title = models.CharField(max_length=100)


class Unregistered(models.Model):
    title = models.CharField(max_length=100)
