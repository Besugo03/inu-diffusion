from flask import Flask, request, jsonify, Response
import requests
import subprocess

from SDGenerator_worker import Txt2ImgJob, ForgeCoupleJob, startGeneration
import JobManager
import defaultsHandler
from imageMetadata import getImageMetadata
import JobManager

import signal
import time
import atexit
import sys
import os

worker_process = None
WORKER_SCRIPT = "./SDGenerator_worker.py"
PYTHON_EXECUTABLE = "venv/Scripts/python.exe" #TODO only windows for now.
WORKER_PID_FILE = "worker.pid" # Define globally
STOP_FLAG_FILE = "stop_worker.flag" # Define globally

def is_worker_running():
    """Checks if the worker process is currently running."""
    global worker_process
    if worker_process and worker_process.poll() is None:
        return True
    if os.path.exists(WORKER_PID_FILE):
        try:
            with open(WORKER_PID_FILE, "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0) 
            # If Popen object exists, verify PID matches or update Popen
            if worker_process and worker_process.pid != pid:
                 print(f"Warning: Popen PID {worker_process.pid} mismatch with PID file {pid}. PID file might be stale or another worker is running.")
            elif worker_process is None: # No Popen, but PID file exists for live process
                 print(f"Info: Worker appears to be running under PID {pid} (from PID file), but not managed by current Flask Popen object.")
            return True
        except (OSError, ValueError, FileNotFoundError):
            if os.path.exists(WORKER_PID_FILE): 
                print(f"Cleaning up stale PID file: {WORKER_PID_FILE}")
                try: os.remove(WORKER_PID_FILE)
                except OSError: pass 
            if worker_process and worker_process.poll() is not None: 
                worker_process = None
            return False
    if worker_process and worker_process.poll() is not None: 
        worker_process = None
    return False

app = Flask(__name__)

SD_BACKEND_URL = "http://127.0.0.1:7860"

@app.route("/txt2img", methods=["POST"])
def txt2img():
    # ADD THIS CHECK AT THE START OF JOB SUBMISSION ROUTES:
    if not is_worker_running():
        return jsonify({"status": "error", "message": "Worker is not running. Please start it first via /start-generation-worker"}), 503
    data = request.get_json()
    print(f'got txt2img job {data["prompt"]}...')

    defaults = defaultsHandler.loadDefaultsFromFile("defaults.json")
    
    generationJob = Txt2ImgJob(
        prompt = "",
        negative_prompt = data.get("negative_prompt", defaults["negative_prompt"]),
        styles = data.get("styles", defaults["styles"]),
        seed = data.get("seed", -1),
        batch_size = 1 ,
        cfg_scale = data.get("cfg_scale", defaults["cfg_scale"]),
        steps = data.get("steps", defaults["steps"]),
        width = 0,
        height = 0,
        sampler = data.get("sampler", defaults["sampler"]),
        enable_hr = data.get("enable_hr", False),
        hr_scale = data.get("hr_scale", 2),
        hr_upscaler = data.get("hr_upscaler", defaults["hr_upscaler"]),
        denoising_strength = data.get("denoising_strength", 0.3),
    )

    width = data.get("width", None)
    height = data.get("height", None)
    if width is None or height is None:
        resolutionList = data.get("resolutionList", defaults["resolutionList"])
    else:
        resolutionList = [(width, height)]

    generator = JobManager.JobGenerator(jobType=generationJob, prompts=[data["prompt"]], resolutionList=resolutionList, numJobs=data["numJobs"])
    generatedTasks = generator.makeTasks()
    jobsave = JobManager.tasksToJob(generatedTasks)

    return {"status" : "success", "message" : jobsave}

@app.route("/txt2imgCouple", methods=["POST"])
def txt2imgCouple():
    # ADD THIS CHECK AT THE START OF JOB SUBMISSION ROUTES:
    if not is_worker_running():
        return jsonify({"status": "error", "message": "Worker is not running. Please start it first via /start-generation-worker"}), 503
    data = request.get_json()
    defaults = defaultsHandler.loadDefaultsFromFile("defaults.json")
    generationJob = ForgeCoupleJob(
        prompt = "",
        negative_prompt = data.get("negative_prompt", defaults["negative_prompt"]),
        styles = data.get("styles", defaults["styles"]),
        seed = data.get("seed", -1),
        batch_size = 1 ,
        cfg_scale = data.get("cfg_scale", defaults["cfg_scale"]),
        steps = data.get("steps", defaults["steps"]),
        width = 0,
        height = 0,
        sampler = data.get("sampler", defaults["sampler"]),
        enable_hr = data.get("enable_hr", False),
        hr_scale = data.get("hr_scale", 2),
        hr_upscaler = data.get("hr_upscaler", defaults["hr_upscaler"]),
        denoising_strength = data.get("denoising_strength", 0.3),
    )

    width = data.get("width", None)
    height = data.get("height", None)
    if width is None or height is None:
        resolutionList = [(1024,1024),(1152,896),(896,1152),(1216,832),(832,1216),(1344,768),(768,1344)]
    else:
        resolutionList = [(width, height)]

    generator = JobManager.JobGenerator(jobType=generationJob, prompts=[data["prompt"]], resolutionList=resolutionList, numJobs=data["numJobs"])
    generatedjobs = generator.makeTasks()
    JobManager.tasksToJob(generatedjobs)

    return jsonify(data)

@app.route("/upscaleTask", methods=["POST"])
def upscaleTask():
    """
    Upscales one or multiple Tasks (images) from a job.
    """
        # ADD THIS CHECK AT THE START OF JOB SUBMISSION ROUTES:
    if not is_worker_running():
        return jsonify({"status": "error", "message": "Worker is not running. Please start it first via /start-generation-worker"}), 503
    import copy
    import json
    from JobManager import getJobs
    import ImageLoadingSaving as ils
    import filelock
    import datetime
    # given a job, it will create a new upscale job, upscaling all images of said job.
    data = request.get_json()

    jobs = getJobs()

    upscalesFrom = str
    upscalesFrom = data["init_images"][0].split("-")[0]

    originalJob = jobs[upscalesFrom]

    # check first if an upscale job for this job already exists
    if "upscalesTo" in originalJob:
        if originalJob["upscalesTo"] != None:
            print("Upscale job already exists for this job.")
            previousUpscaleJob = originalJob["upscalesTo"]
                    
            foundImagesToUpscale = False
            images = data["init_images"]
            images = [image.split(".png")[0] for image in images] # remove .png
            print(f"images to upscale: {images}")
            for image in images:
                upscaleImageTask = f"{image}-u"
                for task in jobs[previousUpscaleJob]["tasks"]:
                    if task["taskID"] == upscaleImageTask:
                        print(f"setting task {task['taskID']} to queued (matches with {upscaleImageTask})")
                        # verify the image still exists
                        try:
                            ils.encode_file_to_base64("./images/" + task["taskID"]+".png")
                        except FileNotFoundError:
                            print(f"File not found for task {task['taskID']}. Deleting task.")
                            jobs[previousUpscaleJob]["tasks"].remove(task)
                            continue
                        foundImagesToUpscale = True
                        task["status"] = "queued"
            if foundImagesToUpscale:
                jobs[previousUpscaleJob]["status"] = "queued"
            
            JobManager.updateJobs(jobs)

            return jsonify({"status": "Upscale job already exists for this job."})
            # TODO implement job modifying

    # create an upscale job from the original job
    # it will contain all the images of the original job
    # same parameters as the original job
    # denoising strength as passed, or 0.4 if not passed
    # upscale the image to 2x the original size or the size passed
    # by default the new upscale job will contain ALL images from the original one, but only the ones that are specified in "init_images" will have "status" : "queued"
    
    originalTasks = jobs[upscalesFrom]["tasks"]
    newTasks = []
    for task in originalTasks:
        newTask = copy.deepcopy(task)
        if "init_images" in data:
            if f'{task["taskID"]}.png' not in data["init_images"]:
                print(f"task {task['taskID']} not in {data['init_images']}, skipping")
                newTask["status"] = None
            else:
                newTask["status"] = "queued"
        else:
            newTask["status"] = "queued"
        
        
        # newTask["init_images"] = [task["init_images"][0]]
        try : 
            givenImageb64 = ils.encode_file_to_base64("./images/" + newTask["taskID"]+".png")
        except FileNotFoundError:
            print(f"File not found for task {newTask['taskID']}. Deleting task.")
            continue
        image_metadata = getImageMetadata("./images/" + newTask["taskID"]+".png")

        newTask["taskID"] = f'{newTask["taskID"]}-u'
        newTask["task"]["width"] = newTask["task"]["width"] * 2
        newTask["task"]["height"] = newTask["task"]["height"] * 2
        newTask["task"]["prompt"] = image_metadata["prompt"]
        newTask["task"]["negative_prompt"] = image_metadata["negative_prompt"]
        newTask["task"]["seed"] = image_metadata["seed"]
        newTask["task"]["sampler"] = image_metadata["sampler_name"]
        newTask["task"]["init_images"] = [givenImageb64]
        newTask["task"]['styles'] = []
        if data.get("denoising_strength", None) != None:
            print(f"setting denoising strength to {data['denoising_strength']}")
            newTask["task"]["denoising_strength"] = data["denoising_strength"]
        
        newTasks.append(newTask)
    
    currentTime = datetime.datetime.now().timestamp()

    jobs[upscalesFrom]["upscalesTo"] = str(currentTime)

    if len(newTasks) == 0:
        print(f"No tasks to upscale for job {upscalesFrom}.")
        return jsonify({"status": "No tasks to upscale for job."})
    
    jobs[currentTime] = {"tasks" : newTasks, "status" : "queued", "jobType" : "upscale"}

    
    JobManager.updateJobs(jobs)
        
    return jsonify({"status": "success", "jobID": currentTime, "upscalesFrom" : upscalesFrom})

@app.route("/upscaleJob", methods=["POST"])
def upscaleJob():
    # ADD THIS CHECK AT THE START OF JOB SUBMISSION ROUTES:
    if not is_worker_running():
        return jsonify({"status": "error", "message": "Worker is not running. Please start it first via /start-generation-worker"}), 503
    import copy
    import json
    from JobManager import getJobs
    import ImageLoadingSaving as ils
    import filelock
    import datetime
    # given a job, it will create a new upscale job, upscaling all images of said job.
    data = request.get_json()
    upscalesFrom = str

    jobs = getJobs()

    # TODO check which images have not been deleted in the job list
        
    upscalesFrom = data["job"]

    originalJob = jobs[upscalesFrom]

    # check first if an upscale job for this job already exists
    if "upscalesTo" in originalJob:
        if originalJob["upscalesTo"] != None:
            print("Upscale job already exists for this job.")
            previousUpscaleJob = originalJob["upscalesTo"]
            # if it's a job-wide upscale, upscale the whole job, skipping the images that are already upscaled
            foundJobsToUpscale = False
            for task in jobs[previousUpscaleJob]["tasks"]:
                if task["status"] == "completed":
                    print(f"task {task['taskID']} is already completed. skipping...")
                    continue
                else:
                    # verify the image still exists
                    try:
                        ils.encode_file_to_base64("./images/" + task["taskID"].split("-u")[0]+".png")
                    except FileNotFoundError:
                        print(f"File ./images/{task['taskID'].split('-u')[0]}.png not found for task {task['taskID']}. Skipping...")
                        # print(f"File not found for task {task['taskID']}. Deleting task.")
                        # jobs[previousUpscaleJob]["tasks"].remove(task)
                        continue
                    foundJobsToUpscale = True
                    task["status"] = "queued"
            if foundJobsToUpscale == False:
                jobs[previousUpscaleJob]["status"] = "queued"
            
            JobManager.updateJobs(jobs)

            return jsonify({"status": "Upscale job already exists for this job."})

    # create an upscale job from the original job
    # it will contain all the images of the original job
    # same parameters as the original job
    # denoising strength as passed, or 0.4 if not passed
    # upscale the image to 2x the original size or the size passed
    # by default the new upscale job will contain ALL images from the original one, but only the ones that are specified in "init_images" will have "status" : "queued"
    originalTasks = jobs[upscalesFrom]["tasks"]
    newTasks = []
    for task in originalTasks:
        newTask = copy.deepcopy(task)
        if "init_images" in data:
            if f'{task["taskID"]}.png' not in data["init_images"]:
                print(f"task {task['taskID']} not in {data['init_images']}, skipping")
                newTask["status"] = None
            else:
                newTask["status"] = "queued"
        else:
            newTask["status"] = "queued"
        
        
        # newTask["init_images"] = [task["init_images"][0]]
        try : 
            givenImageb64 = ils.encode_file_to_base64("./images/" + newTask["taskID"]+".png")
        except FileNotFoundError:
            print(f"File not found for task {newTask['taskID']}. Deleting task.")
            continue
        image_metadata = getImageMetadata("./images/" + newTask["taskID"]+".png")

        newTask["taskID"] = f'{newTask["taskID"]}-u'
        newTask["task"]["width"] = newTask["task"]["width"] * 2
        newTask["task"]["height"] = newTask["task"]["height"] * 2
        newTask["task"]["prompt"] = image_metadata["prompt"]
        newTask["task"]["negative_prompt"] = image_metadata["negative_prompt"]
        newTask["task"]["seed"] = image_metadata["seed"]
        newTask["task"]["sampler"] = image_metadata["sampler_name"]
        newTask["task"]["init_images"] = [givenImageb64]
        newTask["task"]['styles'] = []
        if data.get("denoising_strength", None) != None:
            print(f"setting denoising strength to {data['denoising_strength']}")
            newTask["task"]["denoising_strength"] = data["denoising_strength"]
        
        newTasks.append(newTask)
    
    currentTime = datetime.datetime.now().timestamp()

    jobs[upscalesFrom]["upscalesTo"] = str(currentTime)

    if len(newTasks) == 0:
        print(f"No tasks to upscale for job {upscalesFrom}.")
        return jsonify({"status": "No tasks to upscale for job."})
    
    jobs[currentTime] = {"tasks" : newTasks, "status" : "queued", "jobType" : "upscale"}
    
    JobManager.updateJobs(jobs)
        
    return jsonify({"status": "success", "jobID": currentTime, "upscalesFrom" : upscalesFrom})

# route to upscale all completed jobs that :
# - are completed
# - are txt2img jobs
# - are not upscaled already
# Once a job is upscaled, it will be deleted from the queue (jobs.json)
@app.route("/upscaleAllJobs", methods=["POST"])
def upscaleAllJobs():
    # ADD THIS CHECK AT THE START OF JOB SUBMISSION ROUTES:
    if not is_worker_running():
        return jsonify({"status": "error", "message": "Worker is not running. Please start it first via /start-generation-worker"}), 503
    import copy
    import json
    from JobManager import getJobs
    import ImageLoadingSaving as ils
    import filelock
    import datetime
    
    upscalesFrom = str

    try :
        data = request.get_json()
    except Exception as e:
        print(f"Error getting json data : {e}")
        data = {}

    jobs = getJobs()

    jobsToAdd = {}
    # TODO add removal of jobs with no tasks in them. maybe.

    for job in jobs:
        print(f"checking job {job}... (jobtype {jobs[job]['jobType']})")
        # check if the job is completed
        if jobs[job]["status"] != "completed":
            print(f"job {job} is not completed. skipping...")
            continue
        # check if the job is a txt2img job
        if not (jobs[job]["jobType"] == "txt2img" or jobs[job]["jobType"] == "forgeCouple") :
            print(f"job {job} is not a txt2img or couple job. skipping...")
            continue

        upscalesFrom = job

        # check first if an upscale job for this job already exists
        if "upscalesTo" in jobs[job]:
            if jobs[job]["upscalesTo"] != None:
                print("Upscale job already exists for this job.")
                previousUpscaleJob = jobs[job]["upscalesTo"]
                print(f"previous upscale job: {previousUpscaleJob}")
                # if it's a job-wide upscale, upscale the whole job, skipping the images that are already upscaled
                foundTasksToUpscale = False
                tasksToRemove = []
                for task in jobs[previousUpscaleJob]["tasks"]:
                    # check if the task is already completed
                    if task["status"] == "completed":
                        print(f"task {task['taskID']} is already completed. skipping...")
                        continue
                    else:
                        # verify the image still exists
                        try:
                            ils.encode_file_to_base64("./images/" + task["taskID"].split("-u")[0]+".png")
                            print(f"task {task['taskID']} is not completed. setting to queued...")
                            foundTasksToUpscale = True
                        except FileNotFoundError:
                            print(f"File not found for task {task['taskID']}. Deleting task.")
                            tasksToRemove.append(task)
                            continue
                        task["status"] = "queued"
                if foundTasksToUpscale == True:
                    jobs[previousUpscaleJob]["status"] = "queued"

                # remove the tasks that were deleted
                for task in tasksToRemove:
                    jobs[previousUpscaleJob]["tasks"].remove(task)

        # create an upscale job from the original job
        # it will contain all the images of the original job
        # same parameters as the original job
        # denoising strength as passed, or 0.4 if not passed
        # upscale the image to 2x the original size or the size passed
        # by default the new upscale job will contain ALL images from the original one, but only the ones that are specified in "init_images" will have "status" : "queued"
        else : 
            print(f"creating upscale job for {job}...")
            originalTasks = jobs[upscalesFrom]["tasks"]
            newTasks = []
            for task in originalTasks:
                newTask = copy.deepcopy(task)
                newTask["status"] = "queued"
                
                # newTask["init_images"] = [task["init_images"][0]]
                try : 
                    givenImageb64 = ils.encode_file_to_base64("./images/" + newTask["taskID"]+".png")
                except FileNotFoundError:
                    print(f"File not found for task {newTask['taskID']}. Deleting task.")
                    # TODO remove the task from the job
                    continue
                image_metadata = getImageMetadata("./images/" + newTask["taskID"]+".png")

                newTask["taskID"] = f'{newTask["taskID"]}-u'
                newTask["task"]["width"] = newTask["task"]["width"] * 2
                newTask["task"]["height"] = newTask["task"]["height"] * 2
                newTask["task"]["prompt"] = image_metadata["prompt"]
                newTask["task"]["negative_prompt"] = image_metadata["negative_prompt"]
                newTask["task"]["seed"] = image_metadata["seed"]
                newTask["task"]["sampler"] = image_metadata["sampler_name"]
                newTask["task"]["init_images"] = [givenImageb64]
                newTask["task"]['styles'] = []
                if data.get("denoising_strength", None) != None:
                    print(f"setting denoising strength to {data['denoising_strength']}")
                    newTask["task"]["denoising_strength"] = data["denoising_strength"]
                
                newTasks.append(newTask)
            
            if len(newTasks) == 0:
                print(f"No tasks to upscale for job {job}.")
                continue

            currentTime = datetime.datetime.now().timestamp()
            print(f"current time: {currentTime}")

            jobs[upscalesFrom]["upscalesTo"] = str(currentTime)
            
            jobsToAdd[currentTime] = {"tasks" : newTasks, "status" : "queued", "jobType" : "upscale"}
    
    for job in jobsToAdd:
        jobs[job] = jobsToAdd[job]

    JobManager.updateJobs(jobs)
    return jsonify({"status": "success"})

@app.route("/saveDefaults", methods=["POST"])
def saveDefaults():
    data = request.get_json()
    defaultsHandler.saveDefaultsToFile(data, "defaults.json")
    return jsonify({"status": "success"})

@app.route("/defaults", methods=["GET"])
def getDefaults():
    defaults = defaultsHandler.loadDefaultsFromFile("defaults.json")
    return jsonify(defaults)

@app.route("/jobs", methods=["GET"])
def getJobs():
    """
    Returns the jobs from the jobs.json file.
    """
    jobs = JobManager.getJobs()
    return jobs

@app.route("/jobInfo", methods=["POST"])
def getJobInfo():
    """
    Returns the job info from the jobs.json file.
    """
    data = request.get_json()
    jobID = data["jobID"]
    jobs = JobManager.getJobs()
    if jobID in jobs:
        return jsonify(jobs[jobID])
    else:
        return jsonify({"status": "error", "message": "Job not found"})
    
@app.route("/deleteJob", methods=["POST"])
def deleteJob():
    """
    Deletes a job from the jobs.json file.
    """
    data = request.get_json()
    jobID = data["jobID"]
    jobs = JobManager.getJobs()
    if jobID in jobs:
        # remove the job from the jobs list
        del jobs[jobID]
        JobManager.updateJobs(jobs)
        print(f"deleted job {jobID}")
        return jsonify({"status": "completed", "message": "Job deleted"})
    else:
        JobManager.updateJobs(jobs)
        print(f"job {jobID} not found")
        
        return jsonify({"status": "completed"})
        return jsonify({"status": "error", "message": "Job not found"})

@app.route("/recreate-image", methods=["POST"])
def recreate_image():
    """
    given either :
    - an image as a base64 string
    - a link to a gelbooru post

    it will recreate the image using gelbooru.py
    """
    data = request.get_json()
    print(f"recreating image {data['image']}")
    if "gelbooruID" in data:
        
        import gelbooru as gb
        
        tags = gb.getPostTags("")
        tags = gb.filterTagsCategory(tags, [0])
        print(tags)
        final = ""
        for tag in tags :
            final+= "\"" + tag + "\"" + ", "
        print(final[:-2])
        tags = ",".join(tags)
        # tags = ir.filterForbiddenWords(tags, ["default", "accessories", "attireAndAccessories", "colors", "bodyFeatures"])
        print(tags)
        pass

    elif "image" in data:
        # TODO implement image recreation
        pass
    else:
        return jsonify({"status": "error", "message": "No image or gelbooruID provided"})
    
    return jsonify({"status": "success"})

# ADD THESE ENTIRE ROUTE DEFINITIONS:
@app.route("/start-generation-worker", methods=["POST"])
def start_worker_endpoint():
    global worker_process
    if is_worker_running():
        pid_to_report = "unknown"
        if worker_process and worker_process.poll() is None : pid_to_report = worker_process.pid
        elif os.path.exists(WORKER_PID_FILE):
            try:
                with open(WORKER_PID_FILE, "r") as f: pid_to_report = f.read().strip()
            except: pass
        return jsonify({"status": "error", "message": f"Worker is already running (PID: {pid_to_report})."}), 400

    try:
        if os.path.exists(STOP_FLAG_FILE):
            os.remove(STOP_FLAG_FILE)

        # check if both the worker script and python executable exist
        if not os.path.exists(WORKER_SCRIPT):
            return jsonify({"status": "error", "message": f"Worker script not found: {WORKER_SCRIPT}"}), 500
        if not os.path.exists(PYTHON_EXECUTABLE):
            return jsonify({"status": "error", "message": f"Python executable not found: {PYTHON_EXECUTABLE}"}), 500

        print(f"Starting {WORKER_SCRIPT} with {PYTHON_EXECUTABLE}...")
        worker_process = subprocess.Popen([PYTHON_EXECUTABLE, WORKER_SCRIPT])
        
        time.sleep(2) 

        if worker_process.poll() is not None:
            stdout, stderr = worker_process.communicate()
            error_message = f"Worker failed to start. Exit code: {worker_process.returncode}."
            if stdout: error_message += f"\nStdout: {stdout.decode(errors='ignore')}"
            if stderr: error_message += f"\nStderr: {stderr.decode(errors='ignore')}"
            print(error_message)
            worker_process = None
            return jsonify({"status": "error", "message": error_message}), 500
        
        if not os.path.exists(WORKER_PID_FILE) and (worker_process and worker_process.poll() is None):
            print(f"Warning: Worker process (PID: {worker_process.pid}) started, but PID file not found after 2 seconds.")

        print(f"Worker started with PID: {worker_process.pid}")
        return jsonify({"status": "success", "message": "Generation worker started.", "pid": worker_process.pid})
    except Exception as e:
        print(f"Failed to start worker: {str(e)}")
        return jsonify({"status": "error", "message": f"Failed to start worker: {str(e)}"}), 500

@app.route("/stop-generation-worker", methods=["POST"])
def stop_worker_endpoint():
    global worker_process
    
    pid_from_file = None
    if os.path.exists(WORKER_PID_FILE):
        try:
            with open(WORKER_PID_FILE, "r") as f: pid_from_file = int(f.read().strip())
        except (ValueError, FileNotFoundError): pass

    current_pid_to_signal = None
    process_object_to_check = None

    if worker_process and worker_process.poll() is None:
        current_pid_to_signal = worker_process.pid
        process_object_to_check = worker_process
    elif pid_from_file:
        try:
            os.kill(pid_from_file, 0) 
            current_pid_to_signal = pid_from_file
            print(f"Worker process object not available, using active PID {pid_from_file} from file.")
        except OSError:
            print(f"PID {pid_from_file} from file is not an active process.")
    
    if not current_pid_to_signal:
        if os.path.exists(STOP_FLAG_FILE): os.remove(STOP_FLAG_FILE)
        if os.path.exists(WORKER_PID_FILE): os.remove(WORKER_PID_FILE)
        return jsonify({"status": "error", "message": "Worker is not running or PID not found."}), 400

    print(f"Attempting to stop SDGenerator_worker (PID: {current_pid_to_signal})...")
    with open(STOP_FLAG_FILE, "w") as f: f.write("stop")

    try:
        print(f"Sending SIGINT to worker PID: {current_pid_to_signal}")
        os.kill(current_pid_to_signal, signal.SIGINT)
    except OSError as e:
        print(f"Could not send SIGINT to PID {current_pid_to_signal}: {e}")

    timeout_seconds = 10; start_time = time.time(); process_exited = False
    while time.time() - start_time < timeout_seconds:
        if process_object_to_check:
            if process_object_to_check.poll() is not None:
                print(f"Worker (PID: {current_pid_to_signal}) exited gracefully with code: {process_object_to_check.returncode}.")
                process_exited = True; break
        else: 
            try: os.kill(current_pid_to_signal, 0)
            except OSError: process_exited = True; print(f"Worker (PID: {current_pid_to_signal}) appears to have exited."); break
        time.sleep(0.5)

    if not process_exited:
        print(f"Worker (PID: {current_pid_to_signal}) did not stop gracefully. Terminating...")
        try:
            os.kill(current_pid_to_signal, signal.SIGTERM) 
            time.sleep(2)
            os.kill(current_pid_to_signal, 0) 
            print("SIGTERM failed, sending SIGKILL...")
            os.kill(current_pid_to_signal, signal.SIGKILL)
        except OSError: print(f"Worker (PID: {current_pid_to_signal}) forcefully stopped after SIGTERM/SIGKILL.")
        except Exception as e: print(f"Unexpected error during forceful stop of PID {current_pid_to_signal}: {e}")

    if worker_process and (worker_process.poll() is not None or (pid_from_file and worker_process.pid == pid_from_file)):
        worker_process = None
    # Worker should remove its own PID file. Flask cleans up stop_flag.
    if os.path.exists(STOP_FLAG_FILE):
        try: os.remove(STOP_FLAG_FILE)
        except OSError: pass
    # Fallback: if PID file still exists and process is gone, remove it.
    if process_exited and os.path.exists(WORKER_PID_FILE):
        try: os.remove(WORKER_PID_FILE)
        except OSError: pass
        
    return jsonify({"status": "success", "message": "Stop signal sent. Worker should stop."})

@app.route("/worker-status", methods=["GET"])
def worker_status_endpoint():
    if is_worker_running():
        pid = "unknown"
        if worker_process and worker_process.poll() is None: pid = worker_process.pid
        elif os.path.exists(WORKER_PID_FILE):
            try:
                with open(WORKER_PID_FILE, "r") as f:
                    pid_val = int(f.read().strip())
                os.kill(pid_val, 0); pid = pid_val
            except: pass 
        return jsonify({"status": "running", "pid": pid})
    else:
        return jsonify({"status": "stopped"})

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def proxy_to_sd_backend(path):
    """
    Proxies requests for undefined paths to the Stable Diffusion backend.
    """
    target_url = f"{SD_BACKEND_URL}/{path}"

    # Preserve query parameters
    if request.query_string:
        target_url += "?" + request.query_string.decode('utf-8')

    print(f"Proxying request: {request.method} {request.full_path} -> {target_url}")

    headers = {key: value for (key, value) in request.headers if key.lower() != 'host'}
    # Add any specific headers you might need or want to modify for the backend
    # headers['X-Forwarded-For'] = request.remote_addr # Example

    try:
        # Make the request to the SD backend
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(), # Get raw body data
            cookies=request.cookies,
            allow_redirects=False, # Handle redirects yourself if necessary
            stream=True, # Important for handling large responses or streaming
            timeout=60 # Set a reasonable timeout (e.g., 60 seconds)
        )

        # Build the response to send back to the client
        # Exclude certain headers that shouldn't be blindly proxied
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [(name, value) for (name, value) in resp.raw.headers.items()
                            if name.lower() not in excluded_headers]
         
        # Use Flask's Response object for streaming
        proxied_response = Response(resp.iter_content(chunk_size=1024*10), # Stream content
                                    status=resp.status_code,
                                    headers=response_headers,
                                    content_type=resp.headers.get('Content-Type'))
        
        return proxied_response

    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to SD backend at {SD_BACKEND_URL}")
        return jsonify({"error": "Could not connect to Stable Diffusion backend API"}), 502 # Bad Gateway
    except requests.exceptions.Timeout:
        print(f"Error: Timeout connecting to SD backend at {SD_BACKEND_URL}")
        return jsonify({"error": "Timeout connecting to Stable Diffusion backend API"}), 504 # Gateway Timeout
    except Exception as e:
        print(f"An unexpected error occurred during proxying: {e}")
        return jsonify({"error": f"Proxy error: {str(e)}"}), 500

def cleanup_on_flask_exit():
    """Attempt to stop the worker if Flask is exiting."""
    global worker_process
    print("Flask app is exiting. Attempting to stop worker if running...")
    if is_worker_running():
        pid_to_stop = None
        if worker_process and worker_process.poll() is None: pid_to_stop = worker_process.pid
        elif os.path.exists(WORKER_PID_FILE):
            try:
                with open(WORKER_PID_FILE, "r") as f: pid_to_stop = int(f.read().strip())
            except: pass
        
        if pid_to_stop:
            if not os.path.exists(STOP_FLAG_FILE):
                with open(STOP_FLAG_FILE, "w") as f: f.write("stop")
            try:
                os.kill(pid_to_stop, signal.SIGINT); time.sleep(1)
                os.kill(pid_to_stop, signal.SIGTERM); time.sleep(1)
                # os.kill(pid_to_stop, signal.SIGKILL) # Be cautious with SIGKILL on exit
                print(f"Sent termination signals to worker PID {pid_to_stop} during Flask exit.")
            except OSError: pass 

    if os.path.exists(STOP_FLAG_FILE):
        try: os.remove(STOP_FLAG_FILE)
        except OSError: pass
    # Don't remove PID file here, worker should do it. If flask crashes, it might be stale.

atexit.register(cleanup_on_flask_exit)

if __name__ == "__main__":
    import tag_filterer as tf
    tf.forbiddenTags = defaultsHandler.loadDefaultsFromFile("defaults.json")["forbidden_tags"]
    
    # subprocess.Popen(["./venv/Scripts/python.exe", "SDGenerator_worker.py"])
    
    # Run the Flask app
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)