import requests
from pathlib import Path
import time

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("bvh_file", type=Path)
parser.add_argument("--server_url", default="http://localhost:5001")

args = parser.parse_args()

server_url = args.server_url
bvh_file = args.bvh_file
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
