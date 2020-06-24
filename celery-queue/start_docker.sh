Xvfb :99 -screen 0 640x480x16 &
celery -A tasks worker --concurrency 1 --loglevel=info