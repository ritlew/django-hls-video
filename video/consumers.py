from channels.generic.websocket import WebsocketConsumer
from celery.result import AsyncResult
import json

from .models import VideoFile

class TestConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        res = AsyncResult(VideoFile.objects.latest('pk').task_id)
        text_data_json = json.loads(text_data)
        data = res.info
        if res.ready():
            data = {"progress": 100}

        self.send(text_data=json.dumps(data))

