from channels.routing import ProtocolTypeRouter, URLRouter

import video.routing

application = ProtocolTypeRouter({
    "websocket": URLRouter(video.routing.websocket_urlpatterns),
})

