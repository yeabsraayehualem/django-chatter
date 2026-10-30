from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from chatter.models import Message
from chatter.registry import get_entry
from chatter.serializers import MessageSerializer, NoteSerializer
from chatter.tracking import messages_for, post_message


class RecordChatter(APIView):
    permission_classes = [IsAuthenticated]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        entry = get_entry(kwargs["model"])
        if entry is None:
            raise NotFound("This record type has no chatter.")
        try:
            self.record = get_object_or_404(entry.model, pk=kwargs["pk"])
        except (TypeError, ValueError, ValidationError):
            raise NotFound("Record not found.")
        for permission in (cls() for cls in entry.permission_classes):
            if not permission.has_permission(request, self):
                self.permission_denied(request, message=getattr(permission, "message", None))
            if not permission.has_object_permission(request, self, self.record):
                self.permission_denied(request, message=getattr(permission, "message", None))

    def get(self, request, model, pk):
        messages = messages_for(self.record).select_related("author").prefetch_related("tracking_values")
        return Response(MessageSerializer(messages, many=True).data)

    def post(self, request, model, pk):
        serializer = NoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = post_message(
            self.record,
            body=serializer.validated_data["body"],
            author=request.user,
            kind=Message.Kind.NOTE,
        )
        return Response(MessageSerializer(message).data, status=201)
