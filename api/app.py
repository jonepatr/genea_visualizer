from fastapi import FastAPI, Request, File, UploadFile
import celery.states as states
import os
from celery import Celery
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse
from uuid import uuid4
from pathlib import Path

UPLOAD_FOLDER = Path("/tmp")
CELERY_BROKER_URL = (os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379"),)
CELERY_RESULT_BACKEND = os.environ.get(
    "CELERY_RESULT_BACKEND", "redis://localhost:6379"
)

celery_workers = Celery(
    "tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND
)

tokens = {
    "system": "zPp683mzwC9S4nwkFMekoJJg5WZzCEX2RdKMDBdDvEEtY2Qz7kav2iSb58hQthQC",
    "user": "j7HgTkwt24yKWfHPpFG3eoydJK6syAsz",
}

app = FastAPI()


def save_tmp_file(upload_file) -> str:
    _, extension = os.path.splitext(upload_file.filename)
    filename = f"{uuid4()}{extension}"

    with (UPLOAD_FOLDER / filename).open("wb") as f:
        f.write(upload_file.file.read())

    return f"/files/{filename}"


def verify_token(headers, path):
    token = headers.get("authorization", "")[7:]
    if tokens["system"] == token:
        return True
    elif not path.startswith("/upload_video") and tokens["user"] == token:
        return True
    else:
        return False


@app.middleware("http")
async def authorize(request: Request, call_next):
    if not verify_token(request.headers, request.scope["path"]):
        return JSONResponse(status_code=401)
    return await call_next(request)


@app.post("/render", response_class=PlainTextResponse)
async def render(file: UploadFile = File(...)):

    bvh_file_uri = save_tmp_file(file)
    print(bvh_file_uri)
    task = celery_workers.send_task("tasks.render", args=[bvh_file_uri], kwargs={})
    return f"/jobid/{task.id}"


@app.get("/jobid/{task_id}")
async def check_job(task_id: str) -> str:
    res = celery_workers.AsyncResult(task_id)
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
    return {"state": res.state, "result": result}


@app.get("/files/{file_name}")
async def files(file_name):
    return FileResponse(str(UPLOAD_FOLDER / file_name))


@app.post("/upload_video", response_class=PlainTextResponse)
def upload_video(file: UploadFile = File(...)) -> str:
    return save_tmp_file(file)
