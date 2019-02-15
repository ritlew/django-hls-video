from django.conf import settings

import json
import os
import shlex
import subprocess
import time
from celery import shared_task

from .models import VideoFile


@shared_task(bind=True)
def process_video_file(self, vid_object_pk):
    vid_object = VideoFile.objects.get(pk=vid_object_pk)

    os.chdir(settings.MEDIA_ROOT + "/video")

    input_file = os.path.basename(vid_object.raw_video_file.name)
    folder_name = os.path.splitext(os.path.basename(input_file))[0] + "_" + str(vid_object.pk)
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)

    ffprobe_command = "ffprobe -v quiet -print_format json -show_format -show_streams " + input_file
    prepared_command = shlex.split(ffprobe_command)
    vid_info = json.loads(subprocess.check_output(prepared_command))

    duration = int(float(vid_info["format"]["duration"]))

    thumbnail_command = \
            "ffmpeg -v quiet -i {} -ss {}.000 -vframes 1 {}".format(
        input_file,
        time.strftime("%H:%M:%S", time.gmtime(int(duration / 2))),
        folder_name + "/thumb.jpg"
    )

    print("Creating thumbnail")
    subprocess.Popen(shlex.split(thumbnail_command)).wait()
    # safe default 128k
    audio_bitrate = 128000
    for stream in vid_info["streams"]:
        if stream["codec_type"] == "video":
            DAR = stream["display_aspect_ratio"].replace(":", "/")
            height = int(stream["height"])
            if height % 120 != 0:
                print( "height not evenly divisible by 120")
        if stream["codec_type"] == "audio":
            audio_bitrate = stream["bit_rate"]

    command = "ffmpeg -v quiet -i {} -progress - -c:v libx264 -c:a aac -b:a {} ".format(
                input_file,
                audio_bitrate
                )
    bitrates = ""
    filters = "-filter_complex '"
    maps = ""
    var_map = "'"

    resolutions = [240, 360, 480, 720, 1080]
    for res in resolutions:
        # don't encode higher than source
        if res > height:
            break
        index = resolutions.index(res)
        bitrates += "-b:v:{} {}k ".format(index, str(400 + index * 300))
        filters += "[0:v]scale=-2:{},setdar={}[o{}];".format(res, DAR, res)
        maps += "-map 0:a:0 -map '[o{}]' ".format(res)
        var_map += "a:{},v:{} ".format(index, index)
    filters = filters[:-1] + "' "
    var_map += "' "

    command += bitrates + filters + maps + "\
            -force_key_frames expr:gte(t,n_forced*4) \
            -f hls -hls_flags single_file -hls_segment_type fmp4  \
            -hls_playlist_type event -hls_playlist 1 -hls_time 4 \
            -var_stream_map " + var_map + " -master_pl_name master.m3u8  \
            " + folder_name + "/%v.m3u8"

    with subprocess.Popen(shlex.split(command), bufsize=1, stdout=subprocess.PIPE) as p:
        for line in p.stdout:
            line = line.decode()
            if "out_time_ms" in line:
                current = int(int(line[line.find("=")+1:]) / 1000000)
                percent = int(100 * current / duration)
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "progress": percent
                    }
                )
                print("{}s of {}s, {}%".format(
                    current,
                    duration,
                    percent
                ))


    print("Finishing up")
    vid_object.processed = True
    vid_object.thumbnail = folder_name + "/thumb.jpg"
    vid_object.mpd_file = folder_name + "/master.m3u8"
    vid_object.raw_video_file.delete()
    vid_object.save()

    print(folder_name + " completed")

