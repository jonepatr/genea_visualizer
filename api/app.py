import json
import os
from uuid import uuid4

from flask import Flask, abort, request, send_from_directory, url_for
from werkzeug import secure_filename

import celery.states as states
from celery import Celery
from flask_httpauth import HTTPTokenAuth

CELERY_BROKER_URL = (os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379"),)
CELERY_RESULT_BACKEND = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379"
)


celery_workers = Celery(
    "tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND
)


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/tmp"
auth = HTTPTokenAuth(scheme="Bearer")

tokens = {
    "system": "zPp683mzwC9S4nwkFMekoJJg5WZzCEX2RdKMDBdDvEEtY2Qz7kav2iSb58hQthQC",
    "user": "j7HgTkwt24yKWfHPpFG3eoydJK6syAsz",
}


@auth.verify_token
def verify_token(token):
    if tokens["system"] == token:
        return True
    elif request.endpoint != "upload_video" and tokens["user"] == token:
        return True
    else:
        return False


def save_tmp_file(file_) -> str:
    _, extension = os.path.splitext(file_.filename)
    filename = f"{uuid4()}{extension}"
    file_.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    return url_for("files", file_name=filename)


@app.route("/upload_video", methods=["POST"])
@auth.login_required
def upload_video() -> str:
    return save_tmp_file(request.files["file"])


@app.route("/files/<file_name>")
@auth.login_required
def files(file_name):
    return send_from_directory(
        directory=app.config["UPLOAD_FOLDER"], filename=file_name
    )


@app.route("/render", methods=["POST"])
@auth.login_required
def render() -> str:
    bvh_file_uri = save_tmp_file(request.files["file"])
    task = celery_workers.send_task("tasks.render", args=[bvh_file_uri], kwargs={})
    return url_for("check_job", task_id=task.id)


@app.route("/jobid/<task_id>")
@auth.login_required
def check_job(task_id: str) -> str:
    res = celery_workers.AsyncResult(task_id)
    print(res, flush=True)
    if res.state == states.PENDING:
        reserved_tasks = celery_workers.control.inspect().reserved()
        tasks = []
        if reserved_tasks:
            tasks_per_worker = celery_workers.control.inspect().reserved().values()
            tasks = [item for sublist in tasks_per_worker for item in sublist]
            found = False
            for task in tasks:
                if task["id"] == task_id:
                    found = True
        result = {"jobs_in_queue": len(tasks)}
    elif res.state == states.FAILURE:
        result = str(res.result)
    else:
        result = res.result
    return json.dumps({"state": res.state, "result": result})
