# genea_visualizer

To start the server localy run `docker-compuse up --build`

The server is a http based and works by uploading a bvh file. You will then recieve a "job id" which you can poll in order to see the progress of your rendering. When it is finished you will receive a URL to a video file that you can download. 
Below are some examples using `curl` and at the bottom of the page (and in the file `example.py`) is a full python example of how this can be used.

```curl -XPOST -H "Authorization:Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz" -F "file=@/path/to/bvh/file.bvh" http://SERVER_URL/render``` 
will return a URI to the current job `/jobid/[JOB_ID]`

`curl -H "Authorization:Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz" http://SERVER_URL/jobid/[JOB_ID]` will return the current job state, which might be

* `{result": {"jobs_in_queue": X}, "state": "PENDING"}`: Which means the job is in the queue and waiting to be rendered. The `jobs_in_queue` property is the total number of jobs waiting to be executed. The order of job execution is not guranteed, which means that this number does not reflect how many jobs there are before the current job, but rather reflects if the server is currently busy or not.

* `{result":{"current": X, "total": Y}, "state": "RENDERING"}`: The job is currently being executed. `current` shows which is the last rendered frame and `total` shows how many frames in total this job will render.

* `{"result": FILE_URL, "state": "SUCCESS"}`: The job ended successfully and the video is available at `http://SERVER_URL/[FILE_URL]`.

* `{"result": ERROR_MSG, "state": "FAILURE"}`: The job ended with a failure and the error message is given in `results`.


In order to retrieve the video: `curl -H "Authorization:Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz" http://SERVER_URL/[FILE_URL] -o result.mp4`


A full python (3.7) example (can also be found in `example.py`):

```
import requests
from pathlib import Path
import time

server_url = "http://localhost:5001"
bvh_file = Path("/Users/pj/Downloads/seman_009__.bvh")
headers = {"Authorization": "Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz"}


render_request = requests.post(
    f"{server_url}/render",
    files={"file": (bvh_file.name, bvh_file.open())},
    headers=headers,
)
job_uri = render_request.text

done = False
while not done:
    response = requests.get(server_url + job_uri, headers=headers).json()
    if response["state"] == "PENDING":
        jobs_in_queue = response["result"]["jobs_in_queue"]
        print(f"pending.. total of {jobs_in_queue} jobs in queue")

    elif response["state"] == "RENDERING":
        current = response["result"]["current"]
        total = response["result"]["total"]
        print(f"currently rendering, {current}/{total} done")

    elif response["state"] == "SUCCESS":
        file_url = response["result"]
        done = True

    elif response["state"] == "FAILURE":
        raise Exception(response["result"])

    else:
        print(response)
        raise Exception("should not happen..")

    time.sleep(10)


video = requests.get(server_url + file_url, headers=headers).content
with open("result.mp4", "wb") as f:
    f.write(video)

```
(os.path.basename(file_name), open(file_name, "rb"))
