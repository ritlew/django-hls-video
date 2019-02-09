import subprocess
import os
import ffmpeg

from .models import VideoFile
from django.conf import settings

from celery import shared_task

@shared_task
def process_video_file(vid_object_pk):
    vid_object = VideoFile.objects.get(pk=vid_object_pk)
    
    os.chdir(settings.MEDIA_ROOT + "/video")
    print(os.getcwd())
    input_file = ffmpeg.input(os.path.basename(vid_object.raw_video_file.name))
    if not os.path.exists("test"):
        os.mkdir("test")

    output_processes = [
        ( # 240p video
            input_file
                .output(
                    "01_rebirth.240.m3u8",
                    vcodec="h264",
                    crf=20,
                    video_bitrate=50000,
                    bufsize=100000,
                    vf="scale=-1:240,setdar=16/9",
                    acodec="aac",
                    ar=48000,
                    audio_bitrate=128000,
                    g=60,
                    keyint_min=60,
                    sc_threshold=0,
                    hls_time=4,
                    hls_playlist_type="vod",
                    hls_segment_filename="test/240p%03d.ts",
                    **{"profile:v": "main"}
                )
                .overwrite_output()
                .run_async()
        ),
        ( # 360p video
            input_file
                .output(
                    "01_rebirth.360.m3u8",
                    vcodec="h264",
                    crf=20,
                    video_bitrate=100000,
                    bufsize=200000,
                    vf="scale=-1:360,setdar=16/9",
                    acodec="aac",
                    ar=48000,
                    audio_bitrate=128000,
                    g=60,
                    keyint_min=60,
                    sc_threshold=0,
                    hls_time=4,
                    hls_playlist_type="vod",
                    hls_segment_filename="test/360p_%03d.ts",
                    **{"profile:v": "main"}
                )
                .overwrite_output()
                .run_async()
        ),
        ( # 480p video
            input_file
                .output(
                    "01_rebirth.480.m3u8",
                    vcodec="h264",
                    crf=20,
                    video_bitrate=250000,
                    bufsize=500000,
                    vf="scale=-1:480,setdar=16/9",
                    acodec="aac",
                    ar=48000,
                    audio_bitrate=128000,
                    g=60,
                    keyint_min=60,
                    sc_threshold=0,
                    hls_time=4,
                    hls_playlist_type="vod",
                    hls_segment_filename="test/480p_%03d.ts",
                    **{"profile:v": "main"}
                )
                .overwrite_output()
                .run_async()
        )
    ]

    for process in output_processes:
        process.wait()

#    p = subprocess.Popen([
#        "MP4Box", "-dash", "1000", "-rap", "-frag-rap",
#        "-profile", "onDemand",
#        "-out", "01_rebirth.mpd", 
#        "01_rebirth.480.mp4",
#        "01_rebirth.360.mp4",
#        "01_rebirth.240.mp4",
#        "01_rebirth.audio.mp4"
#    ])

#    p.wait()

    vid_object.processed = True
    vid_object.save()

    return 
