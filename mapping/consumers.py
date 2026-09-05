from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import MapRequest


def map_build_group_name(request_id: int) -> str:
    return f"mapping_build_{int(request_id)}"


class MapBuildConsumer(AsyncJsonWebsocketConsumer):
    """Streams map-building events to the browser for one MapRequest."""

    async def connect(self):
        self.request_id = int(self.scope["url_route"]["kwargs"]["request_id"])
        user = self.scope.get("user")

        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        if not await self._can_access_request(user.id, self.request_id):
            await self.close(code=4403)
            return

        self.group_name = map_build_group_name(self.request_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({
            "type": "connection_ready",
            "request_id": self.request_id,
        })

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "ping":
            await self.send_json({"type": "pong", "request_id": self.request_id})

    async def map_build_event(self, event):
        await self.send_json(event["payload"])

    @database_sync_to_async
    def _can_access_request(self, user_id: int, request_id: int) -> bool:
        return MapRequest.objects.filter(id=request_id, user_id=user_id).exists()
