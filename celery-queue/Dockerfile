FROM ubuntu

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
ENV C_FORCE_ROOT true

RUN apt-get update

RUN apt-get -y install python3-pip wget
RUN mkdir /blender && cd /blender && wget -q https://mirror.clarkson.edu/blender/release/Blender2.83/blender-2.83.0-linux64.tar.xz && tar xf /blender/blender-2.83.0-linux64.tar.xz && rm -r /blender/blender-2.83.0-linux64.tar.xz 

#copy the shared lib for blender 
RUN apt-get install -y libx11-6 build-essential git subversion cmake libx11-dev libxxf86vm-dev libxcursor-dev libxi-dev libxrandr-dev libxinerama-dev libglew-dev
RUN apt-get install -y ffmpeg


RUN apt-get install -y xvfb
COPY . /queue
WORKDIR /queue

RUN pip3 install -r requirements.txt

ENV API_SERVER http://web:5001
ENV DISPLAY :99
ENTRYPOINT bash start_docker.sh
# ENTRYPOINT celery -A tasks worker --loglevel=info
# ENTRYPOINT /blender/blender-2.83.0-linux64/blender -noaudio -b --python blender_render.py
