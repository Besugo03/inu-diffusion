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

# generic class which will be used to handle the requests.
# it contains the endpoint to which the request will be sent,
# the payload which will be sent in the request, and the method
# which will be used to send the request.
class Txt2ImgJob:
    def __init__(self,
        prompt,
        negative_prompt,
        styles = [],
        seed = -1,
        batch_size = 1,
        steps = 25,
        cfg_scale = 5,
        width = 1024,
        height = 1024,
        sampler = "Euler",
        enable_hr = False,
        hr_scale = 2,
        hr_upscaler = "2xHFA2kAVCSRFormer_light",
        denoising_strength = 0.4):
        self.prompt = prompt
        self.negative_prompt = negative_prompt
        self.styles = styles
        self.seed = seed
        self.batch_size = batch_size
        self.steps = steps
        self.cfg_scale = cfg_scale
        self.width = width
        self.height = height
        self.sampler = sampler
        self.save_images = True
        self.enable_hr = enable_hr
        self.hr_scale = hr_scale
        self.hr_upscaler = hr_upscaler
        self.denoising_strength = denoising_strength
        self.endpoint = f"http://{address}/sdapi/v1/txt2img"


    def to_dict(self):
        return {
            "prompt": self.prompt,
            "negative_prompt": self.negative_prompt,
            "styles": self.styles,
            "seed": self.seed,
            "batch_size": self.batch_size,
            "steps": self.steps,
            "cfg_scale": self.cfg_scale,
            "width": self.width,
            "height": self.height,
            "sampler": self.sampler,
            "save_images": self.save_images,
            "enable_hr": self.enable_hr,
            "hr_scale": self.hr_scale,
            "hr_upscaler": self.hr_upscaler,
            "denoising_strength": self.denoising_strength,
            "hr_second_pass_steps": self.steps,
            "hr_sampler_name": "Euler",
            "hr_additional_modules": [],
        }

# superclass "ForgeCoupleJob" which will be used to handle the requests
# for the ForgeCouple script.
class ForgeCoupleJob(Txt2ImgJob):
    def __init__(self, prompt,
        negative_prompt,
        styles = [],
        seed = -1,
        batch_size = 1,
        steps = 25,
        cfg_scale = 5,
        width = 1024,
        height = 1024,
        sampler = "Euler",
        enable_hr = False,
        hr_scale = 2,
        denoising_strength = 0.4,
        hr_upscaler = "2xHFA2kAVCSRFormer_light",
                 enable=True, compatibility=True, mode="Basic", couple_separator="NEXT", tile_direction="Horizontal",
                 global_effect : Literal["First Line", "Last Line", "None"] = "None", global_effect_strength=0.8):
        # initialize the superclass and set the new attributes if they are not None
        super().__init__(prompt, negative_prompt, styles, seed, batch_size, steps, cfg_scale, width, height, sampler, enable_hr=enable_hr, hr_scale=hr_scale, hr_upscaler=hr_upscaler, denoising_strength=denoising_strength)
        self.enable = enable
        self.compatibility = compatibility
        self.mode = mode
        self.couple_separator = couple_separator
        self.tile_direction = tile_direction
        self.global_effect = global_effect
        self.global_effect_strength = global_effect_strength
        self.endpoint = f"http://{address}/sdapi/v1/txt2img"

    def to_dict(self):
        data = super().to_dict()
        data["alwayson_scripts"] = {
            "forge couple": {
                "args": [
                    self.enable,
                    self.compatibility,
                    self.mode,
                    self.couple_separator,
                    self.tile_direction,
                    self.global_effect,
                    self.global_effect_strength
                ]
            }
        }
        return data

class SDRequestHandler:
    def __init__(self, address):
        self.address = address

    def send_job(self, job : Txt2ImgJob):
        endpoint = job.endpoint
        payload = job.to_dict()
        success = False
        while not success:
            try:
                response = requests.post(endpoint, json=payload)
                success = True
            except Exception as e:
                print(f"Error sending request: {str(e)}")
                # wait for 1 second before retrying
                import time
                time.sleep(1)
                pass
        return response


class JobGenerator:
    def __init__(self, job : Txt2ImgJob|ForgeCoupleJob, prompts: list, resolutionList: list, numJobs : int):
        self.job = job
        self.prompts = prompts
        self.resolutionList = resolutionList
        self.numJobs = numJobs
    
    def makeJobs(self) -> list[Txt2ImgJob|ForgeCoupleJob]:
        import random
        import copy
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

handler = SDRequestHandler(address)

testcouplejob = Txt2ImgJob(
    prompt="test",
    negative_prompt="vagina, pussy, huge breasts, bangs,",
    # global_effect_strength=0.7,
    height=1152,
    width=896,
    batch_size=1,
    cfg_scale=5,
    styles=["WAI-Illustrious-newerStyle"],
    # global_effect="Last Line",
    # enable_hr = True,
    # denoising_strength=0.3,
)

tf.forbiddenTags += ["deflor","vagin","puss","breast","loli","shota","monst","demon","tail","horn","futa","amput","severing","guro","blood"]

basePrompt = ""

promptList = [
    basePrompt + "",
]

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

# for i in testJobsList:
#     response = handler.send_job(i)
#     print(f"job {i.to_dict()} sent")
#     # print(response.json())
job_queue = queue.Queue()

generator = JobGenerator(testcouplejob, promptList,[(1024,1024),(1152,896),(896,1152),(1216,832),(832,1216),(1344,768),(768,1344)], 2)

# --- Memory Setting Code ---
# ... (same as before)
# --- End Memory Setting ---

import filelock
import json
# Function for worker threads to execute

# --- Main Thread Logic ---

# Add initial jobs
initial_jobs = generator.makeJobs()
# for job in initial_jobs:
#     handler.send_job(job)


def saveJobs(jobs):
    import datetime
    import json
    import filelock
    jobEntry = {datetime.datetime.now().timestamp() : { "tasks" : [{ "job" : job.to_dict(), "completed" : False} for job in jobs], "completed" : False}}
    print(jobEntry)
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


saveJobs(initial_jobs)
# print([job.to_dict() for job in initial_jobs])
# print(loadJobs() == [job.to_dict() for job in initial_jobs])

# print(loadJobs())

# print(f"Adding {len(initial_jobs)} initial jobs to the queue...")
# for job in initial_jobs:
#     job_queue.put(job)

# # Simulate adding more jobs after a short delay while workers are running
# print("Waiting a bit before adding more jobs...")
# time.sleep(5) # Wait 5 seconds (adjust as needed)

# more_jobs = generator.makeJobs()
# print(f"Adding {len(more_jobs)} more jobs to the queue...")
# for job in more_jobs:
#     job_queue.put(job)

# # --- Wait for all jobs to be processed ---
# print("Waiting for all jobs in the queue to be processed...")
# job_queue.join() # Blocks until all items have been gotten and task_done() called for each

# print("All jobs processed. Signaling workers to stop...")
# # Signal workers to stop by adding None sentinel values
# for _ in range(MAX_WORKERS):
#     job_queue.put(None)

# # Wait for worker threads to exit (optional but good practice if not daemon)
# # for t in threads:
# #     t.join()

# print("Processing finished.")