FROM python:3.7.2-alpine
ENV PYTHONBUFFERED 1

ARG USER

RUN apk update && apk add git postgresql-dev linux-headers alpine-sdk coreutils git nasm x264-dev

# FFMPEG 4.1 clone and build
WORKDIR /opt
RUN git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg
WORKDIR /opt/ffmpeg
RUN git checkout release/4.1
RUN ./configure --enable-gpl --enable-libx264 --prefix=/usr && make -j4 && make install

# django project
RUN mkdir /code
WORKDIR /code

ADD ./requirements.txt /code

RUN pip install -r requirements.txt
ADD ./progress_bar.js /usr/local/lib/python3.7/site-packages/progressbarupload/static/js/progress_bar.js

