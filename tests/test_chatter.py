from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from chatter import register
from chatter.tracking import log_changes, messages_for, post_message, snapshot
from tests.testapp.models import Document, Secret, Ticket, Unregistered

User = get_user_model()


class ChatterTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user("abebe", first_name="Abebe", last_name="Kebede")
        self.client.force_authenticate(self.user)

    def test_integer_primary_key(self):
        ticket = Ticket.objects.create(title="A")
        response = self.client.post(f"/chatter/ticket/{ticket.pk}/", {"body": " Hello "}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["author"], {"id": self.user.pk, "name": "Abebe Kebede"})
        self.assertEqual(self.client.get(f"/chatter/ticket/{ticket.pk}/").json()[0]["body"], "Hello")

    def test_uuid_primary_key(self):
        document = Document.objects.create(title="A")
        post_message(document, body="Created.")
        messages = self.client.get(f"/chatter/doc/{document.pk}/").json()
        self.assertEqual([(m["kind"], m["body"], m["author"]) for m in messages], [("system", "Created.", None)])
        self.assertEqual(messages_for(document).get().record, document)

    def test_author_without_full_name_falls_back_to_str(self):
        user = User.objects.create_user("noname")
        self.client.force_authenticate(user)
        ticket = Ticket.objects.create(title="A")
        response = self.client.post(f"/chatter/ticket/{ticket.pk}/", {"body": "Hi"}, format="json")
        self.assertEqual(response.json()["author"]["name"], "noname")

    def test_tracking_reads_like_the_ui(self):
        ticket = Ticket.objects.create(title="A")
        fields = ["status", "owner", "watchers"]
        before = snapshot(ticket, fields)
        ticket.status = Ticket.Status.DONE
        ticket.owner = self.user
        ticket.save()
        ticket.watchers.set([self.user])
        message = log_changes(ticket, before, fields, self.user, labels={"owner": "Assigned to"})
        values = {v.field: (v.field_label, v.old_value, v.new_value) for v in message.tracking_values.all()}
        self.assertEqual(values, {
            "status": ("Status", "Open", "Done"),
            "owner": ("Assigned to", "", "Abebe Kebede"),
            "watchers": ("Watchers", "", "Abebe Kebede"),
        })

    def test_no_change_logs_nothing(self):
        ticket = Ticket.objects.create(title="A")
        self.assertIsNone(log_changes(ticket, snapshot(ticket, ["title"]), ["title"]))
        self.assertFalse(messages_for(ticket).exists())

    def test_child_logs_on_parent(self):
        parent, child = Ticket.objects.create(title="P"), Document.objects.create(title="A")
        before = snapshot(child, ["title"])
        Document.objects.filter(pk=child.pk).update(title="B")
        log_changes(child, before, ["title"], record=parent)
        self.assertEqual(messages_for(parent).count(), 1)
        self.assertFalse(messages_for(child).exists())

    def test_same_pk_on_two_models_stays_separate(self):
        first, second = Ticket.objects.create(title="A"), Secret.objects.create(pk=1, title="B")
        self.assertEqual(first.pk, second.pk)
        post_message(first, body="Ticket only")
        self.assertFalse(messages_for(second).exists())

    def test_access_rules(self):
        secret = Secret.objects.create(title="A")
        self.assertEqual(self.client.get(f"/chatter/secret/{secret.pk}/").status_code, 403)
        self.client.force_authenticate(User.objects.create_user("staff", is_staff=True))
        self.assertEqual(self.client.get(f"/chatter/secret/{secret.pk}/").status_code, 200)
        self.assertIn(self.client_class().get(f"/chatter/secret/{secret.pk}/").status_code, (401, 403))

    def test_not_found(self):
        unregistered = Unregistered.objects.create(title="A")
        for url in (
            f"/chatter/unregistered/{unregistered.pk}/",
            "/chatter/ticket/999/",
            "/chatter/ticket/not-a-number/",
            "/chatter/doc/not-a-uuid/",
        ):
            self.assertEqual(self.client.get(url).status_code, 404, url)


class RegistryTests(SimpleTestCase):
    def test_name_clash_is_rejected(self):
        with self.assertRaises(ImproperlyConfigured):
            register(Secret, name="ticket")
