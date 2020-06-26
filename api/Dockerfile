FROM python:3.8-alpine

ENV CELERY_BROKER_URL redis://redis:6379/0
ENV CELERY_RESULT_BACKEND redis://redis:6379/0
ENV C_FORCE_ROOT true

ENV HOST 0.0.0.0
ENV PORT 5001
ENV DEBUG true

# Prompt non-interactive
ENV DEBIAN_FRONTEND=noninteractive

RUN apk add build-base
RUN pip install uvicorn==0.11.5 uvloop==0.14.0

COPY . /api
WORKDIR /api

# install requirements
RUN pip install -r requirements.txt

# expose the app port
EXPOSE 5001


# run the app server
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "5001", "--workers", "4", "app:app"]
