# GENEA 2020 BVH Visualizer
<p align="center">
  <img src="gesture.gif" alt="example from visualization server">
  <br>
  <i>Example output from the visualization server</i>
</p>


This repository provides scripts that can be used to visualize BVH files. These scripts were developed for the [GENEA Challenge 2020](https://genea-workshop.github.io/2020/#gesture-generation-challenge), and enables reproducing the visualizations used for the challenge stimuli.
The server consists of several containers which are launched together with the docker-compose command described below.
The components are:
* web: this is the HTTP server which receives render requests and places them on a "celery" queue to be processed.
* worker: this takes jobs from the "celery" queue and works on them. Each worker runs one Blender process, so increasing the amount of workers adds more parallelization. 
* monitor: this is a monitoring tool for celery. Default username is `user` and password is `password` (can be changed by setting `FLOWER_USER` and `FLOWER_PWD` when starting the docker-compose command)
* redis: needed for celery


## Build and start visualization server
First you need to install docker-compose:
`sudo apt  install docker-compose` (on Ubuntu)

You might want to edit some of the default parameters, such as render resolution and fps, in the `.env` file.

Then to start the server run `docker-compose up --build`

In order to run several (for example 3) workers (Blender renderers, which allows to parallelize rendering, run `docker-compose up --build --scale worker=3`

The `-d` flag can also be passed in order to run the server in the background. Logs can then be accessed by running `docker-compose logs -f`. Additionally it's possible to rebuild just the worker or API containers with minimal disruption in the running server by running for example `docker-compose up -d --no-deps --scale worker=2 --build worker`. This will rebuild the worker container and stop the old ones and start 2 new ones.

## Use the visualization server
The server is HTTP-based and works by uploading a bvh file. You will then receive a "job id" which you can poll in order to see the progress of your rendering. When it is finished you will receive a URL to a video file that you can download. 
Below are some examples using `curl` and in the file `example.py` there is a full python (3.7) example of how this can be used.

Since the server is available publicly online, a simple authentication system is included – just pass in the token `j7HgTkwt24yKWfHPpFG3eoydJK6syAsz` with each request. This can be changed by modifying `USER_TOKEN` in `.env`.

For a simple usage example, you can see a full python script in `example.py`.

Otherwise, you can follow the detailed instructions on how to use the visualization server provided below.

Depending on where you host the visualization, `SERVER_URL` might be different. If you just are running it locally on your machine you can use `127.0.0.1` but otherwise you would use the ip address to the machine that is hosting the server.

```curl -XPOST -H "Authorization:Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz" -F "file=@/path/to/bvh/file.bvh" http://SERVER_URL/render``` 
will return a URI to the current job `/jobid/[JOB_ID]`.

`curl -H "Authorization:Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz" http://SERVER_URL/jobid/[JOB_ID]` will return the current job state, which might be any of:
* `{result": {"jobs_in_queue": X}, "state": "PENDING"}`: Which means the job is in the queue and waiting to be rendered. The `jobs_in_queue` property is the total number of jobs waiting to be executed. The order of job execution is not guaranteed, which means that this number does not reflect how many jobs there are before the current job, but rather reflects if the server is currently busy or not.
* `{result": null, "state": "PROCESSING"}`: The job is currently being processed. Depending on the file size this might take a while, but this acknowledges that the server has started to working on the request.
* `{result":{"current": X, "total": Y}, "state": "RENDERING"}`: The job is currently being rendered, this is the last stage of the process. `current` shows which is the last rendered frame and `total` shows how many frames in total this job will render.
* `{"result": FILE_URL, "state": "SUCCESS"}`: The job ended successfully and the video is available at `http://SERVER_URL/[FILE_URL]`.
* `{"result": ERROR_MSG, "state": "FAILURE"}`: The job ended with a failure and the error message is given in `results`.

In order to retrieve the video, run `curl -H "Authorization:Bearer j7HgTkwt24yKWfHPpFG3eoydJK6syAsz" http://SERVER_URL/[FILE_URL] -o result.mp4`. Please note that the server will delete the file after you retrieve it, so you can only retrieve it once!

## Replicating the GENEA Challenge 2020 visualizations
The parameters in the enclosed file `docker-compose-genea.yml` correspond to those that were used to render the final evaluation stimuli of the GENEA Challenge, for ease of replication.

### If you use this code in your research please cite our IUI article:
```
@inproceedings{kucherenko2021large,
  author = {Kucherenko, Taras and Jonell, Patrik and Yoon, Youngwoo and Wolfert, Pieter and Henter, Gustav Eje},
  title = {A Large, Crowdsourced Evaluation of Gesture Generation Systems on Common Data: {T}he {GENEA} {C}hallenge 2020},
  year = {2021},
  isbn = {9781450380171},
  publisher = {Association for Computing Machinery},
  address = {New York, NY, USA},
  url = {https://doi.org/10.1145/3397481.3450692},
  doi = {10.1145/3397481.3450692},
  booktitle = {26th International Conference on Intelligent User Interfaces},
  pages = {11--21},
  numpages = {11},
  keywords = {evaluation paradigms, conversational agents, gesture generation},
  location = {College Station, TX, USA},
  series = {IUI '21}
}
```
