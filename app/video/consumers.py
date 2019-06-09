from channels.generic.websocket import WebsocketConsumer
from celery.result import GroupResult
from collections import namedtuple
import json

from .models import Video

VideoResult = namedtuple('VideoResult', ['video', 'task'])

class UploadProgressConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        upload_ids = text_data_json.get("upload_ids", None)

        currently_processing = []

        if upload_ids:
            processing_videos = Video.objects.filter(upload_id__in=upload_ids)
        else:
            processing_videos = Video.objects.filter(processed=False)

        for video in processing_videos:
            result = GroupResult.restore(video.processing_id)
            if result:
                currently_processing.append(VideoResult(video, result))

        response = {'uploads': []}
        for item in currently_processing:
            item_info = {
                'upload_id': str(item.video.upload_id),
                'title': item.video.title,
                'slug': item.video.slug,
                'processed': item.video.processed,
            }

            for results in item.task.results:
                if results.info:
                    response['uploads'].append({
                        **item_info,
                        **results.info
                    })
            else:
                response['uploads'].append(item_info)

        self.send(text_data=json.dumps(response))

