from flask import Flask, request, jsonify
import subprocess

from SDGenerator_worker import Txt2ImgJob, ForgeCoupleJob, startGeneration
import JobManager
import defaultsHandler
from imageMetadata import getImageMetadata

app = Flask(__name__)

@app.route("/txt2img", methods=["POST"])
def txt2img():
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
    JobManager.tasksToJob(generatedTasks)

    return jsonify(data)

@app.route("/txt2imgCouple", methods=["POST"])
def txt2imgCouple():
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
            
            lock = filelock.FileLock("jobs.json.lock", timeout=10) # 10 seconds timeout for lock
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
    
    JobManager.updateJobs(jobs)
        
    return jsonify({"status": "success", "jobID": currentTime, "upscalesFrom" : upscalesFrom})

@app.route("/upscaleJob", methods=["POST"])
def upscaleJob():
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
                    continue
                else:
                    # verify the image still exists
                    try:
                        ils.encode_file_to_base64("./images/" + task["taskID"]+".png")
                    except FileNotFoundError:
                        print(f"File not found for task {task['taskID']}. Deleting task.")
                        jobs[previousUpscaleJob]["tasks"].remove(task)
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
    
    JobManager.updateJobs(jobs)
        
    return jsonify({"status": "success", "jobID": currentTime, "upscalesFrom" : upscalesFrom})

# route to upscale all completed jobs that :
# - are completed
# - are txt2img jobs
# - are not upscaled already
# Once a job is upscaled, it will be deleted from the queue (jobs.json)
@app.route("/upscaleAllJobs", methods=["POST"])
def upscaleAllJobs():
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

if __name__ == "__main__":
    import tag_filterer as tf
    tf.forbiddenTags = defaultsHandler.loadDefaultsFromFile("defaults.json")["forbidden_tags"]
    subprocess.Popen(["./venv/Scripts/python.exe", "SDGenerator_worker.py"])
    # Run the Flask app
    app.run()