from django.urls import re_path

from .consumers import MapBuildConsumer


websocket_urlpatterns = [
    re_path(r"^ws/mapping/build/(?P<request_id>\d+)/$", MapBuildConsumer.as_asgi()),
]
