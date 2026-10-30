from rest_framework.permissions import IsAdminUser

from chatter import register
from tests.testapp.models import Document, Secret, Ticket

register(Ticket)
register(Document, name="doc")
register(Secret, permission_classes=[IsAdminUser])
