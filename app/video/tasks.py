import json
import m3u8
import os
import shlex
import subprocess
import time

from celery import shared_task
from celery.result import allow_join_result
from django.conf import settings
from django.db import transaction
from itertools import filterfalse
from time import strftime, gmtime

from .models import VideoChunkedUpload, VideoUpload, Video, VideoVariant, RESOLUTIONS


@shared_task(bind=True)
def setup_video_processing(self, video_pk):
    # change to media directory
    os.chdir(settings.MEDIA_ROOT)

    print("Saving video")
    with transaction.atomic():
        video = Video.objects.get(pk=video_pk)
        chunked_upload = VideoChunkedUpload.objects.get(upload_id=video.upload.upload_id)
        video.upload.raw_video_file = chunked_upload.get_uploaded_file()
        video.upload.save()
    print("Saving completed")

    upload_filepath = video.upload.raw_video_file.name

    # create the video folder name
    folder_path = os.path.relpath(
        os.path.join(
            settings.SENDFILE_ROOT,
            'video',
            os.path.splitext(os.path.basename(upload_filepath))[0] + f'_{video.upload.pk}'
        )
    )

    # create video folder
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)

    # get info about video
    ffprobe_command = f'ffprobe -v quiet -print_format json -show_format -show_streams {upload_filepath}'
    prepared_command = shlex.split(ffprobe_command)
    vid_info_str = subprocess.check_output(prepared_command).decode()

    # save gained data to video object
    with transaction.atomic():
        video = Video.objects.get(pk=video_pk)
        video.vid_info_str = vid_info_str
        video.folder_path = folder_path
        video.save()

    return


@shared_task(bind=True)
def create_thumbnail(self, video_pk):
    # get the upload object
    video = Video.objects.get(pk=video_pk)

    # change to media directory
    os.chdir(settings.MEDIA_ROOT)

    # get video duration in seconds
    duration = int(float(video.vid_info['format']['duration']))

    # create thumbnail command for ffmpeg
    thumbnail_timestamp = strftime('%H:%M:%S', gmtime(int(duration / 2)))
    thumbnail_command = \
       f'ffmpeg -v quiet -hide_banner -i {video.upload.raw_video_file.name} ' \
       f'-ss {thumbnail_timestamp}.000 -vframes 1 {video.folder_path}/thumb.jpg'
    subprocess.Popen(shlex.split(thumbnail_command)).wait()

    with transaction.atomic():
        video = Video.objects.get(pk=video_pk)
        video.thumbnail = os.path.join(video.folder_path, "thumb.jpg")
        video.save()

    return


@shared_task(bind=True)
def create_variants(self, video_pk):
    # get the upload object
    video = Video.objects.get(pk=video_pk)

    # change to media directory
    os.chdir(settings.MEDIA_ROOT)

    for stream in video.vid_info['streams']:
        if stream['codec_type'] == 'video':
            # force original video display aspect resolution
            DAR = stream['display_aspect_ratio'].replace(':', '/')
            # video height
            height = int(stream['height'])
            if height % 120 != 0:
                print('Height not evenly divisible by 120')

    # start ffmpeg command
    command = f'ffmpeg -v quiet -i {video.upload.raw_video_file.name} -progress - -c:a aac -ac 2 -c:v libx264 -crf 20 '

    # working variables to build stream specific parts of command
    bitrates = ''
    filters = "-filter_complex '"
    maps = ''
    var_map = "'"

    # parallel array with RESOLUTION
    BITRATES = [350, 700, 1200, 2500, 5000]

    # count encoded resolutions
    last = 0
    for i, res in enumerate(RESOLUTIONS):
        # don't encode higher than source
        if res > height:
            break
        last = i
        bitrates += "-b:v:{} {}k ".format(i, BITRATES[i])
        filters += "[0:v]scale=-2:{},setdar={}[o{}];".format(res, DAR, res)
        maps += "-map '[o{}]' ".format(res)
        var_map += "v:{},agroup:aud ".format(i, i)

        # save variant
        variant = VideoVariant(
            master=video,
            playlist_file=os.path.join(video.folder_path, f'{i}.m3u8'),
            video_file=os.path.join(video.folder_path, f"{i}.m4s"),
            resolution=i
        )
        variant.save()

    # cap off command parts
    filters = filters[:-1] + "' "
    maps += "-map 0:a:0"
    var_map += "a:0,agroup:aud'"

    # audio-only variant
    variant = VideoVariant(
        master=video,
        playlist_file=os.path.join(video.folder_path, f'{last+1}.m3u8'),
        video_file=os.path.join(video.folder_path, f'{last+1}.m4s'),
        resolution=last+1
    )
    variant.save()

    # combine into final command
    command += f'{bitrates} {filters} {maps} \
            -force_key_frames expr:gte(t,n_forced*4) \
            -f hls -hls_flags single_file -hls_segment_type fmp4  \
            -hls_playlist_type event -hls_playlist 1 -hls_time 4 \
            -var_stream_map {var_map} -master_pl_name master.m3u8 \
            {video.folder_path}/%v.m3u8'

    # get total video duration
    duration = int(float(video.vid_info["format"]["duration"]))

    with subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE) as p:
        for line in p.stdout:
            line = line.decode()
            # only look for out_time_ms which is the current amount
            # of video that has been encoded in terms of time
            if 'out_time_ms' in line:
                # get encoded time in seconds
                current = int(line[line.find('=')+1:]) / 1000000
                percent = 100 * current / duration

                # update the result for user
                self.update_state(
                    state="P" + str(int(percent)),
                    meta={
                        'progress': round(percent, 2),
                        'current': int(current),
                        'total': duration
                    }
                )
                # update developer who doesn't want to be left in the dark
                # while testing this encoding function for the 1000th time
                # because one component isn't working quite right
                print(f'{current}s of {duration}s, {percent}%')

    # remove audio-only variants from master playlist
    # as they won't play with videojs
    master_playlist_filepath = os.path.join(video.folder_path, 'master.m3u8')
    master = m3u8.load(master_playlist_filepath)
    master.playlists[:] = filterfalse(lambda x: x.stream_info.codecs == 'mp4a.40.2', master.playlists)
    master.dump(master_playlist_filepath)

    with transaction.atomic():
        video = Video.objects.get(pk=video_pk)
        video.processed = True
        video.master_playlist = os.path.join(video.folder_path, 'master.m3u8')
        video.upload.raw_video_file.delete()
        video.save()
    return

