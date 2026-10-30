from django.urls import include, path

urlpatterns = [path("chatter/", include("chatter.urls"))]
