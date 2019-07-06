from channels.generic.websocket import WebsocketConsumer
from celery.result import AsyncResult
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
        # requested list of videos
        upload_ids = text_data_json.get("upload_ids", None)

        # if there are specific requested videos
        if upload_ids:
            processing_videos = Video.objects.filter(upload_id__in=upload_ids)
        else:
            # otherwise, return all processing videos
            processing_videos = Video.objects.filter(processed=False)

        # get all results available for queried videos
        currently_processing = []
        for video in processing_videos:
            if video.processing_id:
                result = AsyncResult(video.processing_id)
                if result:
                    currently_processing.append(VideoResult(video, result))
                else:
                    currently_processing.append(VideoResult(video, None))
            else:
                currently_processing.append(VideoResult(video, None))


        # create response dictionary
        response = {'uploads': []}
        # for every processing video
        for item in currently_processing:
            item_info = {
                'upload_id': str(item.video.upload_id),
                'title': item.video.title,
                'slug': item.video.slug,
                'processed': item.video.processed,
            }
            if item.task:
                if item.task.info:
                    # put data in response
                    item_info = {
                        **item_info,
                        **item.task.info
                    }
                if item.task.state:
                    item_info = {
                        **{'state': item.task.state},
                        **item_info,
                    }
            response['uploads'].append(item_info)

        self.send(text_data=json.dumps(response))

