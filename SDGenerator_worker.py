from typing import Literal
import signal
import os

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
        infotext = "",
        alwayson_scripts = {}):
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
        enable=True, 
        compatibility=True, 
        mode="Basic", 
        couple_separator="NEXT", 
        tile_direction="Horizontal",
        global_effect : Literal["First Line", "Last Line", "None"] = "None", 
        global_effect_strength=0.8,
        save_images = True,
        hr_second_pass_steps = 20,
        hr_sampler_name = "Euler",
        hr_additional_modules = [],
        infotext = "",
        alwayson_scripts = {}):
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

shutdown_signal_received = False
WORKER_PID_FILE = "worker.pid" # Define globally
STOP_FLAG_FILE = "stop_worker.flag" # Define globally

def signal_handler(signum, frame):
    global shutdown_signal_received
    print(f"WORKER: Signal {signum} received. Initiating graceful shutdown...")
    shutdown_signal_received = True
    # Optionally create stop_worker.flag here too as a fallback
    with open(STOP_FLAG_FILE, "w") as f:
        f.write("stop")

# TODO add the other kinds of job (couple, img2img, etc)
def send_job(job : Txt2ImgJob, taskName = None):
    import requests
    endpoint = job.endpoint
    payload = job.to_dict()
    success = False
    while not success:
        try:
            print(f"sending request to server on endpoint {endpoint}... ")
            print(f"payload: {payload}")
            response = requests.post(endpoint, json=payload)
            print(f"response: {response}")
            print("test")
            success = True
            print(f"response status code: {response.status_code}")
            if response.status_code != 200:
                print(f"Error: Received status code {response.status_code} from server.")
                print(f"Response text: {response.text}")
                raise Exception(f"Server returned status code {response.status_code}")
        except Exception as e:
            print(f"Error sending request: {str(e)}")
            # wait for 1 second before retrying
            import time
            time.sleep(1)
            pass
    import ImageLoadingSaving as ils
    # print the json keys of the response
    # print(response.json())
    # print(len(response.json()["images"]))
    import os
    os.makedirs("./images", exist_ok=True)

    jobs = loadJobs()
    print(f"saving image for task {taskName}...")
    print(f"response json keys: {response.json().keys()}")
    print(response.json()["images"][0][0:30], "...") # print the first 30 characters of the image data
    ils.save_image(ils.decode_image(response.json()["images"][0]), f"./images/{taskName}.png")
    # add the metadata to the image (info)
    metadata = response.json()["info"]
    # convert the metadata (string) to a dictionary
    import json
    metadata = json.loads(metadata)
    metadata = {"parameters" : metadata}
    # print(metadata)
    # print(isinstance(metadata, dict))
    ils.add_metadata_to_image(f"./images/{taskName}.png", metadata)
    
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
            taskName = None
            # print(jobs)
            for job in jobs:
                if jobs[job]["status"] == "queued" and foundJob is None:
                    for task in jobs[job]["tasks"]:
                        foundJob = job
                        foundTask = task
                        taskName = task['taskID']
                        if task["status"] == "queued":
                            job = task["task"]
                            break
                    break
            if foundTask is None: # Sentinel value to signal shutdown
                print("[WORKER] found no jobs to process. Exiting...")
                return False
            # print(f"found task : '{foundTask['job']['prompt']}' from job: {foundJob}")

            try:
                print(f"[WORKER] found task : '{foundTask['taskID']}' from job: {foundJob}")
                print(f"[WORKER] jobtype : {jobs[foundJob]['jobType']}")
                if jobs[foundJob]["jobType"] == "txt2img":
                    job = Txt2ImgJob(**foundTask["task"])
                elif jobs[foundJob]["jobType"] == "forgeCouple":
                    job = ForgeCoupleJob(**foundTask["task"])
                    script_args = foundTask['task'].get("alwayson_scripts", {}).get("forge couple", {}).get("args", [])
                    job.enable = script_args[0]
                    job.compatibility = script_args[1]
                    job.mode = script_args[2]
                    job.couple_separator = script_args[3]
                    job.tile_direction = script_args[4]
                    job.global_effect = script_args[5]
                    print(f"[WORKER] global_effect: {job.global_effect}")
                    job.global_effect_strength = script_args[6]
                elif jobs[foundJob]["jobType"] == "upscale":
                    job = UpscaleJob(**foundTask["task"])
                else:
                    print(f"[WORKER] Unknown job type: {foundJob['jobType']}. Skipping...")
                    return True

                # Send the job to the server
                print(f"[WORKER] sending job: {job.prompt.strip()[0:50]}... to server")
                response = send_job(job, taskName=taskName)
                # print("response : ",response.json())

                lock = filelock.FileLock("jobs.json.lock", timeout=10) # 10 seconds timeout for lock
                with lock:
                    newjobs = loadJobs(lock)
                    if newjobs != jobs:
                        print("[WORKER] jobs have changed while processing. Updating jobs...")
                        jobs = newjobs
                    # set the task to completed
                    if foundTask is not None:
                        jobs[foundJob]["tasks"][jobs[foundJob]["tasks"].index(foundTask)]["status"] = "completed"
                        print(f"[WORKER] set task {foundTask['taskID']} to completed")
                    # if all tasks are completed or None set the job to completed
                    if all(task["status"] == "completed" or task["status"] == None for task in jobs[foundJob]["tasks"]):
                        jobs[foundJob]["status"] = "completed"
                        print(f"[WORKER] set job {foundJob} to completed")
                    # save the jobs to the file
                    with open("jobs.json", "w", encoding="utf-8") as f:
                        json.dump(jobs, f, indent=4)
                        f.close()
                        print("[WORKER] saved jobs to file")

            except Exception as e:
                raise e
                #  print(e)
            finally:
                print(f"[WORKER] finished job")
                # print(f"finished job {job}")
                return True
                
        except Exception as e:
            raise e
            print(f"encountered error: {e}")
            # if job is not None:
            #    try:
            #        job_queue.task_done() # Try to mark done even on error to avoid deadlock on join()
            #    except ValueError: # May happen if task_done called twice
            #        pass

def main_worker_loop_function():
    import time
    global shutdown_signal_received
    print(f"WORKER: Started with PID {os.getpid()}. Polling for jobs...")
    while not shutdown_signal_received:
        if os.path.exists(STOP_FLAG_FILE):
            print("WORKER: Stop flag file detected. Shutting down...")
            shutdown_signal_received = True # Ensure flag is set
            break # Exit loop

        # Your existing startGeneration() logic call
        processed_job = startGeneration() # Modify startGeneration to return True if job processed, False if no job

        if shutdown_signal_received: # Check after a potential blocking call
            break

        if not processed_job: # If no job was found/processed by startGeneration
            # Sleep but make it interruptible and check flags often
            for _ in range(10): # e.g. 1 second total if sleep is 0.1
                if shutdown_signal_received or os.path.exists(STOP_FLAG_FILE):
                    shutdown_signal_received = True
                    break
                time.sleep(0.1)
        if shutdown_signal_received: # Final check in loop iteration
             break
    print("WORKER: Exiting main loop.")

if __name__ == "__main__":
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        with open(WORKER_PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except IOError:
        print(f"Could not write PID file {WORKER_PID_FILE}. Exiting...")
        exit(1)

    try:
        main_worker_loop_function() # Your existing while True loop logic moved here
    finally:
        print("WORKER: Cleaning up PID and flag files...")
        if os.path.exists(WORKER_PID_FILE):
            try: os.remove(WORKER_PID_FILE)
            except OSError as e: print(f"WORKER: Error removing PID file: {e}")
        if os.path.exists(STOP_FLAG_FILE):
            try: os.remove(STOP_FLAG_FILE)
            except OSError as e: print(f"WORKER: Error removing stop flag file: {e}")
        print("SDGenerator_worker shut down.")