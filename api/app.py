# Copyright 2020 by Patrik Jonell.
# All rights reserved.
# This file is part of the GENEA visualizer,
# and is released under the GPLv3 License. Please see the LICENSE
# file that should have been included as part of this package.


import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import celery.states as states
from celery import Celery
from fastapi import BackgroundTasks, FastAPI, File, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse

UPLOAD_FOLDER = Path("/tmp/genea_visualizer")
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


celery_workers = Celery(
    "tasks",
    broker=os.environ["CELERY_BROKER_URL"],
    backend=os.environ["CELERY_RESULT_BACKEND"],
)

app = FastAPI()


async def save_tmp_file(upload_file) -> str:
    _, extension = os.path.splitext(upload_file.filename)
    filename = f"{uuid4()}{extension}"
    (UPLOAD_FOLDER / filename).write_bytes(upload_file.file.read())
    return f"/files/{filename}"


def verify_token(headers, path):
    token = headers.get("authorization", "")[7:]
    if os.environ["SYSTEM_TOKEN"] == token:
        return True
    elif not path.startswith("/upload_video") and os.environ["USER_TOKEN"] == token:
        return True
    else:
        return False


async def delete_tmp_file(file: Path):
    file.unlink()


async def remove_old_tmp_files():
    for file in UPLOAD_FOLDER.glob("*"):
        time_delta = datetime.now() - datetime.fromtimestamp(os.path.getmtime(file))
        if time_delta.days > 0:
            file.unlink()


@app.middleware("http")
async def authorize(request: Request, call_next):
    if not verify_token(request.headers, request.scope["path"]):
        return JSONResponse(status_code=401)
    return await call_next(request)


@app.post("/render", response_class=PlainTextResponse)
async def render(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    bvh_file_uri = await save_tmp_file(file)
    task = celery_workers.send_task("tasks.render", args=[bvh_file_uri], kwargs={})
    background_tasks.add_task(remove_old_tmp_files)
    return f"/jobid/{task.id}"


@app.get("/jobid/{task_id}")
def check_job(task_id: str) -> str:
    res = celery_workers.AsyncResult(task_id)
    if res.state == states.PENDING:
        reserved_tasks = celery_workers.control.inspect().reserved()
        tasks = []
        if reserved_tasks:
            tasks_per_worker = reserved_tasks.values()
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
    return {"state": res.state, "result": result}


@app.get("/files/{file_name}")
async def files(file_name, background_tasks: BackgroundTasks):
    file = UPLOAD_FOLDER / file_name
    background_tasks.add_task(delete_tmp_file, file)
    return FileResponse(str(file))


@app.post("/upload_video", response_class=PlainTextResponse)
async def upload_video(file: UploadFile = File(...)) -> str:
    return await save_tmp_file(file)
