FROM python:3.6.8-alpine
ENV PYTHONBUFFERED 1

RUN apk update && apk add git postgresql-dev linux-headers alpine-sdk coreutils git nasm x264-dev libffi-dev

# FFMPEG 4.1 clone and build
WORKDIR /opt
RUN git clone --single-branch --branch release/4.1 https://git.ffmpeg.org/ffmpeg.git ffmpeg
WORKDIR /opt/ffmpeg
RUN ./configure --enable-gpl --enable-libx264 --prefix=/usr && make -j4 && make install

# django project
RUN mkdir /code
WORKDIR /code
COPY app/requirements.txt /code/requirements.txt

RUN pip install -r requirements.txt
 
COPY ./config/uwsgi/sites/django-hls-video /code/

