from typing import Literal

address = "127.0.0.1:7860"
# TODO move the generation classes somewhere else bc it doesnt make sense to have them here
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
        infotext = "",
        enable_hr = False,
        hr_scale = 2,
        hr_upscaler = "2xHFA2kAVCSRFormer_light",
        denoising_strength = 0.4,
        save_images = True,
        hr_second_pass_steps = 20,
        hr_sampler_name = "Euler",
        hr_additional_modules = []):
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
        self.infotext = infotext


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
            "infotext": self.infotext,
        }

class UpscaleJob(Txt2ImgJob):
    # TODO add that, if you specify an upscaler, it uses that to send to extras and then do the inference
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
        denoising_strength = 0.4,
        hr_second_pass_steps = 20,
        hr_sampler_name = "Euler",
        hr_additional_modules = [],
        save_images = True,
        init_images = [],
        metadata = "",
        infotext = "",):
        super().__init__(prompt, negative_prompt, styles, seed, batch_size, steps, cfg_scale, width, height, sampler, infotext)
        # super().__init__("", negative_prompt, styles, seed, batch_size, steps, cfg_scale, width, height, sampler)
        self.init_images = init_images
        self.metadata = metadata
        # print(f"init_images: {self.init_images[0][0:30]}...")
        self.endpoint = f"http://{address}/sdapi/v1/img2img"
    def to_dict(self):
        data = super().to_dict()
        data["init_images"] = self.init_images
        data["metadata"] = self.metadata
        return data

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


# TODO add the other kinds of job (couple, img2img, etc)
def send_job(job : Txt2ImgJob, jobID = None, taskIndex = None):
    import requests
    endpoint = job.endpoint
    payload = job.to_dict()
    payloadCopy = payload.copy()
    payloadCopy["init_images"] = ["<hidden>"]
    print(f"Sending request to {endpoint} with payload: {payloadCopy}")
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
    import ImageLoadingSaving as ils
    # print the json keys of the response
    print(response.json().keys())
    print(len(response.json()["images"]))
    import os
    os.makedirs("./images", exist_ok=True)
    ils.save_image(ils.decode_image(response.json()["images"][0]), f"./images/{jobID}-{taskIndex}.png")
    return response

def loadJobs(lock = None):
    import json
    import filelock
    try:
        if not lock:
            lock = filelock.FileLock("jobs.json.lock", timeout=10) # 10 seconds timeout for lock
        with lock:
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
    return jobList

    
def startGeneration():
        import filelock
        import json
        try:
            # Get a job from the queue. Blocks if empty.
            # Use timeout to allow checking for shutdown signal periodically if needed
            # job = job_queue.get(timeout=1)

            jobs = loadJobs()
            # find the first job that is not completed
            foundJob = None
            foundTask = None
            foundTaskIndex = None
            # print(jobs)
            for job in jobs:
                if jobs[job]["completed"] != True and foundJob is None:
                    for task in jobs[job]["tasks"]:
                        foundJob = job
                        foundTask = task
                        foundTaskIndex = jobs[job]["tasks"].index(task)
                        if task["completed"] != True:
                            job = task["job"]
                            break
                    break
            if foundTask is None: # Sentinel value to signal shutdown
                print("found no jobs to process. Exiting...")
                return
            # print(f"found task : '{foundTask['job']['prompt']}' from job: {foundJob}")

            try:
                print(f"jobtype : {jobs[foundJob]['jobType']}")
                if jobs[foundJob]["jobType"] == "txt2img":
                    job = Txt2ImgJob(**foundTask["job"])
                elif jobs[foundJob]["jobType"] == "forgeCouple":
                    job = ForgeCoupleJob(**foundTask["job"])
                elif jobs[foundJob]["jobType"] == "upscale":
                    job = UpscaleJob(**foundTask["job"])
                else:
                    print(f"Unknown job type: {foundJob['jobType']}. Skipping...")
                    return
                
                # TODO remove Simulate work
                # import time
                # time.sleep(1)

                # Send the job to the server
                response = send_job(job, jobID=foundJob, taskIndex=foundTaskIndex)
                print("response : ",response.json())

                lock = filelock.FileLock("jobs.json.lock", timeout=10) # 10 seconds timeout for lock
                with lock:
                    newjobs = loadJobs(lock)
                    if newjobs != jobs:
                        print("jobs have changed while processing. Updating jobs...")
                        jobs = newjobs
                    # set the task to completed
                    if foundTask is not None:
                        jobs[foundJob]["tasks"][jobs[foundJob]["tasks"].index(foundTask)]["completed"] = True
                    # if all tasks are completed, set the job to completed
                    if all(task["completed"] == True for task in jobs[foundJob]["tasks"]):
                        jobs[foundJob]["completed"] = True
                    # save the jobs to the file
                    with open("jobs.json", "w", encoding="utf-8") as f:
                        json.dump(jobs, f, indent=4)
                        f.close()

            except Exception as e:
                raise e
                #  print(e)
            finally:
                print(f"finished job")
                # print(f"finished job {job}")
                
        except Exception as e:
            raise e
            print(f"encountered error: {e}")
            # if job is not None:
            #    try:
            #        job_queue.task_done() # Try to mark done even on error to avoid deadlock on join()
            #    except ValueError: # May happen if task_done called twice
            #        pass

if __name__ == "__main__":
    import time
    while True:
        startGeneration()
        time.sleep(1)