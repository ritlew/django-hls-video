#!/bin/bash

set -x

vid=01_rebirth.mkv
filename=$(basename -- "$vid")
extension="${filename##*.}"
filename="${filename%.*}"



ffmpeg -hide_banner -loglevel panic -y -i $vid -c:a aac -ac 2 -ab 128k -vn "$filename".audio.mp4


: '
ffmpeg -y -i $vid -an -c:v libx264 \
	-x264opts 'keyint=30:min-keyint=30:no-scenecut' \
	-b:v 1060k -maxrate 1060k -bufsize 530k \
	-vf 'scale=-1:480,setdar=16:9' "$filename".480.mp4 &


ffmpeg -y -i $vid -an -c:v libx264 \
	-x264opts 'keyint=30:min-keyint=30:no-scenecut' \
	-b:v 600k -maxrate 600k -bufsize 300k \
	-vf 'scale=-1:360,setdar=16:9' "$filename".360.mp4 &
'

ffmpeg -hide_banner -loglevel panic -y -i $vid -an -c:v libx264 \
	-x264opts 'keyint=30:min-keyint=30:no-scenecut' \
	-b:v 260k -maxrate 260k -bufsize 130k \
	-vf 'scale=-1:240,setdar=16:9' "$filename".240.mp4

MP4Box -dash 1000 -rap -frag-rap -profile onDemand \
	-out "$filename".mpd \
        "$filename".240.mp4 \
	"$filename".audio.mp4
