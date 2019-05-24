from channels.generic.websocket import WebsocketConsumer
from celery.result import GroupResult
import json

from .models import Video

class TestConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        group_res = GroupResult.restore(
            Video.objects.get(upload__upload_id=text_data_json["upload_id"]).processing_id
        )
        
        data = {}
        for res in group_res.results:
            if res.info:
                data = res.info

        if group_res.ready():
            data = {
                'progress': 100,
            }

        self.send(text_data=json.dumps(data))

