import os
import time
from celery import Celery
import subprocess
import sys
from celery.utils.log import get_task_logger
import pickle
import requests
import tempfile
from pyvirtualdisplay import Display

Display().start()


logger = get_task_logger(__name__)

CELERY_BROKER_URL = (os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379"),)
CELERY_RESULT_BACKEND = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379"
)
API_SERVER = os.environ.get("API_SERVER", "http://localhost:5001")


celery = Celery("tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

headers = {
    "Authorization": "Bearer zPp683mzwC9S4nwkFMekoJJg5WZzCEX2RdKMDBdDvEEtY2Qz7kav2iSb58hQthQC"
}


class TaskFailure(Exception):
    pass


@celery.task(name="tasks.render", bind=True)
def render(self, bvh_file_uri: str) -> str:
    logger.info("rendering..")

    bvh_file = requests.get(API_SERVER + bvh_file_uri, headers=headers).content

    with tempfile.NamedTemporaryFile(suffix=".bhv") as tmpf:
        tmpf.write(bvh_file)
        tmpf.seek(0)
        process = subprocess.Popen(
            [
                "/blender/blender-2.83.0-linux64/blender",
                "-noaudio",
                "-b",
                "--python",
                "blender_render.py",
                "--",
                tmpf.name
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        total = None
        current_frame = None
        for line in process.stdout:
            line = line.decode("utf-8").strip()
            if line.startswith("total_frames "):
                _, total = line.split(" ")
                total = int(float(total))
            elif line.startswith("Append frame "):
                *_, current_frame = line.split(" ")
                current_frame = int(current_frame)
            elif line.startswith("output_file"):
                _, file_name = line.split(" ")
                files = {"file": (os.path.basename(file_name), open(file_name, "rb"))}
                return requests.post(
                    API_SERVER + "/upload_video", files=files, headers=headers
                ).text
            if total and current_frame:
                self.update_state(
                    state="RENDERING", meta={"current": current_frame, "total": total}
                )
        if process.returncode != 0:
            raise TaskFailure(process.stderr.read().decode("utf-8"))
