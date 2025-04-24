import queue
import time
import threading
from typing import Literal
import requests
import instant_wildcard as iw
import tag_filterer as tf
# import threadpoolexecutor
import concurrent.futures

address = "127.0.0.1:7860"


class JobGenerator:
    """
    A class to generate jobs for the Stable Diffusion generator.
    It takes a base job and generates multiple jobs with different
    prompts and resolutions, starting from it.

    **prompts**: list of prompts to use for the jobs. This can be empty, and if so, it will use the base job's prompt.
    
    **resolutionList**: list of tuples containing the resolutions to use for the jobs.

    **numJobs**: number of jobs to generate for each prompt.
    """
    from SDGenerator_worker import Txt2ImgJob, ForgeCoupleJob, UpscaleJob
    def __init__(self, job : Txt2ImgJob|ForgeCoupleJob|UpscaleJob, prompts: list, resolutionList: list, numJobs : int):
        self.job = job
        self.prompts = prompts
        self.resolutionList = resolutionList
        self.numJobs = numJobs
    
    def makeJobs(self) -> list[Txt2ImgJob|ForgeCoupleJob|UpscaleJob]:
        import random
        import copy
        from SDGenerator_worker import Txt2ImgJob, ForgeCoupleJob, UpscaleJob
        jobsList = []
        if self.prompts == [] or self.prompts == None:
            self.prompts = [self.job.prompt]
        for prompt in self.prompts:
            for i in range(self.numJobs):
                newJob = copy.deepcopy(self.job)
                chosenRes = random.choice(self.resolutionList)
                newJob.width = chosenRes[0]
                newJob.height = chosenRes[1]
                newJob.prompt = iw.process_wildcard_prompt(prompt)
                jobsList.append(newJob)
        return jobsList

# set the memory first to avoid slow inference
testdatamemory = {"forge_inference_memory": 5000}
success = False
while not success:
    try :
        requests.post(f"http://{address}/sdapi/v1/options", json=testdatamemory)
        success = True
    except Exception as e:
        print(f"Error setting memory: {str(e)}")
        # wait for 1 second before retrying
        import time
        time.sleep(1)
        pass

def saveJobs(jobs):
    import datetime
    import json
    import filelock
    jobType = type(jobs[0])
    if jobType == JobGenerator.Txt2ImgJob:
        jobType = "txt2img"
    elif jobType == JobGenerator.ForgeCoupleJob:
        jobType = "forgeCouple"
    elif jobType == JobGenerator.UpscaleJob:
        jobType = "upscale"
    jobEntry = {datetime.datetime.now().timestamp() : { "tasks" : [{ "job" : job.to_dict(), "completed" : False} for job in jobs], "completed" : False, "jobType" : jobType}}
    # print(jobEntry)
    lock = filelock.FileLock("jobs.json.lock", timeout=10) # 10 seconds timeout for lock
    with lock:
        try:
            with open("jobs.json", "r", encoding="utf-8") as f:
                jobList = json.load(f)
                f.close()
        except FileNotFoundError:
            print("No job file found. Creating a new one...")
            jobList = {}
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading job file : {e}. Starting with empty list.")
            return []
        except filelock.Timeout:
            print(f"Could not acquire lock for file. Cannot load jobs.")
            # Decide how to handle this - maybe exit or wait longer
            return []

        jobList.update(jobEntry)
        with open("jobs.json", "w", encoding="utf-8") as f:
            json.dump(jobList, f, indent=4)
            f.close()