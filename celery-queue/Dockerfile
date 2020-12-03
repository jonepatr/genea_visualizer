FROM ubuntu:18.04


ENV C_FORCE_ROOT true
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get -y install python3-pip wget ffmpeg xvfb python-opengl
RUN mkdir /blender && cd /blender && wget -q https://mirror.clarkson.edu/blender/release/Blender2.83/blender-2.83.0-linux64.tar.xz && tar xf /blender/blender-2.83.0-linux64.tar.xz && rm -r /blender/blender-2.83.0-linux64.tar.xz 

COPY . /queue
WORKDIR /queue

RUN pip3 install -r requirements.txt

ENTRYPOINT celery -A tasks worker --concurrency 1 --loglevel=info