import json
import base64
import metadata
import PIL
from PIL import Image
import requests
import os
import b64encoder as encoder
import instant_wildcard as iw

# handles the scheduling of jobs.

# json is formatted the following way:
# { "job_ID" : { "job_type" : job_type, "status" : status, "starting_img" : starting_image_dir } }
# }
# job type is either "txt2img", "txt2imgVariations", "img2img"
# status is either pending, done, or failed.
# starting_img is the directory of the image that started the job.

default_endpoint : str
stableDiffusionDir = "/mnt/Lexar 2TB/stable-diffusion-webui-forge/"

def update_job_in_json(job_ID, job_type = None, starting_img_path = None):
    """### Save a job to the jobs.json file.
    Syntax : 
    job1 :{
	status : "done" / "pending",
    job_type : "txt2img" / "txt2imgVar" / "img2img",
	starting_img : starting_img_dir,
	output_images : [
		imagePath1,
		imagePath2,
		imagePath3,
		...
		],
	images_checked : True / False,
	}"""

    with open("jobs.json", "r") as file:
        # if the file is empty, set jobs to an empty dictionary
        try :
            jobs = json.load(file)
        except json.decoder.JSONDecodeError:
            jobs = {}
        
    starting_img = str
    if job_type == "txt2img" :  starting_img = None
    elif starting_img_path : starting_img = starting_img_path
    else : starting_img = jobs[job_ID]["starting_img"]
    
    jobs[job_ID] = {
        "job_type" : job_type if job_type is not None else jobs[job_ID]["job_type"],
        "status" : get_job_status(job_ID),
        "starting_img" : starting_img,
        "output_images" : [] if get_output_images(job_ID) is None else get_output_images(job_ID), # grid images are not considered
        # the images checked stays the same if the job was already in the json file, otherwise it is set to False.
        "images_checked" : jobs[job_ID]["images_checked"] if job_ID in jobs else False
    }

    # if the job is an img2img job, it's done and it has been checked, we can remove its starting image from the original txt2img job.
    if job_type == "img2img" and jobs[job_ID]["status"] == "done" and jobs[job_ID]["images_checked"] == True:
        # the original job is the job that generated the image that was used for the img2img job.
        original_job = None
        for job in jobs: # for each job
            if jobs[job]["output_images"] is not None: # if the job has output images
                if starting_img_path in jobs[job]["output_images"]:
                    original_job = job
        if original_job is not None:
            print(f"original job for {job_ID}  : {original_job}")
            original_job_images = jobs[original_job]["output_images"]
            print(starting_img_path)
            original_job_images.remove(starting_img_path)
            jobs[original_job]["output_images"] = original_job_images

    # if there are no output images and the album is checked,
    # it means that the images have been deleted, so we remove the job from the json file.
    if jobs[job_ID]["output_images"] == [] and jobs[job_ID]["images_checked"] == True:
        jobs.pop(job_ID)
    with open("jobs.json", "w") as file:
        json.dump(jobs, file, indent=4)

def get_jobs_from_json():
    """### Get all the jobs from the jobs.json file."""
    try:
        with open("jobs.json", "r") as file:
            jobs = json.load(file)
    except json.decoder.JSONDecodeError: # if the file is empty, return an empty dictionary
        jobs = {}
    return jobs

def update_all_jobs_in_json():
    """### Update all the jobs in the jobs.json file."""
    jobs = get_jobs_from_json()
    for job_ID in jobs:
        update_job_in_json(job_ID)

def remove_job_from_json(job_ID):
    """### Remove a job from the jobs.json file."""
    with open("jobs.json", "r") as file:
        jobs = json.load(file)
    try : 
        jobs.pop(job_ID)
    except KeyError:
        print(f"Job {job_ID} not found in the jobs.json file.")
    with open("jobs.json", "w") as file:
        json.dump(jobs, file)

def queue_img2img(
        image_path=None,
        width=None, height=None,
        # tiling=True, # to check if tiling is actually vae or something else
        denoising_strength = 0.2,
        upscale_factor = 2,
        lora_multiplier = 0.5,
        prompt = None, 
        negative_prompt = None, 
        batch_size = 1, 
        sampler_name = "Euler a", 
        # styles = ["BlushySpicy Style"],
        steps = 25,
        cfg_scale = 7, 
        checkpoint = "autismmixSDXL_autismmixPony.safetensors",
        vae = "sdxl_vae.safetensors", 
        seed = None):

    """### Queue a img2img job to the agent scheduler.
    returns an object with the job ID if successful."""

    # in case a local SD path was given (output/...) make it an absolute path
    # this is the case if it's invoked from other functions that work like this
    if stableDiffusionDir not in image_path:
        image_path = stableDiffusionDir+image_path

    # open the image and encode it in base64 to send it to the API
    with open(image_path, 'rb') as file:
        image_data = file.read()
    encoded_image = base64.b64encode(image_data).decode('utf-8')

    # if either width or height is not specified, set them the dimensions of the specified image
    # (go to the local image path), get the dimensions and set them to width and height
    if width is None or height is None:
        with Image.open(image_path) as img:
            width, height = img.size
            width = width * upscale_factor
            height = height * upscale_factor

    url = default_endpoint + "/agent-scheduler/v1/queue/img2img"
    headers = {"Content-Type": "application/json"}

    image_prompts = metadata.extract_prompt(image_path)
    
    if prompt is None : prompt = image_prompts[0]
    if negative_prompt is None : negative_prompt = image_prompts[1]
    if seed is None : seed = metadata.extract_seed(image_path)

    prompt = metadata.reduce_lora_strength(prompt, lora_multiplier)

    data = {
        "init_images" : [encoded_image],
        "denoising_strength": denoising_strength,
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        # "styles": styles,
        "seed": seed,
        "sampler_name": sampler_name,
        "batch_size": batch_size,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "width": width,
        "height": height,
        "restore_faces": False,
        "tiling": False,
        "checkpoint": checkpoint,
        "vae": vae,
        "do_not_save_samples": False,
        "do_not_save_grid": False
    }
    response = requests.post(url, headers=headers, json=data)
    task_id = response.json()["task_id"]
    # remove stableDiffusionDir from the image path
    image_path = image_path.replace(stableDiffusionDir, "")
    update_job_in_json(task_id, "img2img", image_path)
    print(f"img2img job started with ID {task_id}")
    return task_id

def queue_txt2img(
        prompt = "", 
        negative_prompt = "", 
        width = 1024 , height = 1024, 
        n_iter = 1,
        batch_size = 1, 
        sampler_name = "Euler a",
        styles = ["BlushySpicy Style"],
        steps = 25,
        cfg_scale = 7, 
        checkpoint = "autismmixSDXL_autismmixPony.safetensors",
        vae = "sdxl_vae.safetensors", 
        seed = -1):
    
    """### Queue a txt2img job to the agent scheduler.
    returns an object with the job ID if successful."""

    url = default_endpoint + "/agent-scheduler/v1/queue/txt2img"
    headers = {"Content-Type": "application/json"}
    # print(styles)
    prompt = iw.process_instant_wildcard_prompt(prompt)
    data = {
        "prompt": prompt,
        "n_iter" : n_iter,
        "negative_prompt": negative_prompt,
        "styles": styles,
        "seed": seed,
        "sampler_name": sampler_name,
        "batch_size": batch_size,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "width": width,
        "height": height,
        "restore_faces": False,
        "tiling": False,
        "checkpoint": checkpoint,
        "vae": vae,
        "do_not_save_samples": False,
        "do_not_save_grid": False,
        "infotext": "test infotext"
    }
    response = requests.post(url, headers=headers, json=data)
    print(response.json())
    print(f'txt2img job started with ID {response.json()["task_id"]}')
    update_job_in_json(response.json()["task_id"], "txt2img")
    return response.json()["task_id"]

def test_txt2img(
        prompt = "", 
        negative_prompt = "", 
        width = 1024 , height = 1024, 
        n_iter = 1,
        batch_size = 1, 
        sampler_name = "Euler a",
        styles = ["BlushySpicy Style"],
        steps = 25,
        cfg_scale = 7, 
        checkpoint = "autismmixSDXL_autismmixPony.safetensors",
        vae = "sdxl_vae.safetensors", 
        seed = -1):
    
    """### Testing stuff with the original API"""

    url = default_endpoint + "/sdapi/v1/txt2img"
    headers = {"Content-Type": "application/json"}
    # print(styles)
    prompt = iw.process_instant_wildcard_prompt(prompt)
    print(f"prompt : {prompt}")
    data = {
        "prompt": prompt,
        "n_iter" : n_iter,
        "negative_prompt": negative_prompt,
        "styles": styles,
        "seed": seed,
        "sampler_name": sampler_name,
        "batch_size": batch_size,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "width": width,
        "height": height,
        "restore_faces": False,
        "tiling": False,
        "checkpoint": checkpoint,
        "vae": vae,
        "do_not_save_samples": False,
        "do_not_save_grid": False,
        # "infotext": "test infotext",
        "save_images": True
    }
    response = requests.post(url, headers=headers, json=data)
    print("test_txt2img response : ")
    print(response.json())
    return response.json()

def queue_txt2imgVariations(
        original_image_path = None,
        n_iter = 3,
        prompt_addon = "",
        negative_prompt_addon = "",
        width = 1024 , height = 1024,
        cfg_scale = 5,
):
    # open the image and get the prompt and negative prompt

    if stableDiffusionDir not in original_image_path:
        original_image_path = stableDiffusionDir+original_image_path

    image_prompts = metadata.extract_prompt(original_image_path)
    prompt = image_prompts[0]
    negative_prompt = image_prompts[1]
    seed = metadata.extract_seed(original_image_path)
    prompt = prompt + prompt_addon
    negative_prompt = negative_prompt + negative_prompt_addon

    # get the width and height of the image
    with Image.open(original_image_path) as img:
        width, height = img.size

    # get the styles of the image

    # queue the txt2img job
    t2ijob = queue_txt2img(prompt, negative_prompt, n_iter=n_iter, width=width, height=height, cfg_scale=cfg_scale, styles=[], seed=-1)
    original_image_path = original_image_path.replace(stableDiffusionDir, "")
    update_job_in_json(t2ijob, "txt2imgVariations", original_image_path)
    return t2ijob

def queue_img2imgFromTask(taskID : str):
    """### Queue an img2img job for each image in a txt2img task.
    returns the jobs IDs if successful."""
    jobs = get_jobs_from_json()
    task = jobs[taskID]
    images = task["output_images"]
    if task["status"] != "done":
        print("Task is not done yet.")
        return
    jobIDs = []
    for image in images:
        jobIDs.append(queue_img2img(image_path=f"{stableDiffusionDir}{image}"))
    return jobIDs

def queue_img2imgAllFinishedJobs():
    """### Queue an img2img job for each image in all the finished txt2img tasks."""
    update_all_jobs_in_json() # update all the jobs in the json file
    jobs = get_jobs_from_json()
    jobIDs = []
    for job in jobs:
        jobtype = jobs[job]["job_type"]
        for image in jobs[job]["output_images"]:
            # make sure to not queue img2img jobs for img2img jobs
            if (jobs[job]["status"] == "done" # if the job is done (maybe not necessary)
                and (jobtype != "img2img")
                and jobs[job]["images_checked"] == True): # if the job has been checked
                # make sure to not queue img2img jobs for images that have been already queued
                already_queued = False
                for otherjob in jobs:
                    if (jobs[otherjob]["starting_img"] == image and jobs[otherjob]["job_type"]=="img2img"):
                        print(f"image {image} already done!")
                        already_queued = True
                        continue
                # if not already_queued : print(f"queueing {image}...")
                queue_img2img(image)
    #  return jobIDs

def queue_VariationsAllChekedJobs():
    """### Queue a txt2imgVariations job for each image in all the finished txt2img tasks."""
    update_all_jobs_in_json() # update all the jobs in the json file
    jobs = get_jobs_from_json()
    jobIDs = []
    for job in jobs:
        jobtype = jobs[job]["job_type"]
        for image in jobs[job]["output_images"]:
            # make sure to not queue txt2imgVariations jobs for txt2imgVariations jobs
            if (jobs[job]["status"] == "done" # if the job is done (maybe not necessary)
                and (jobtype == "txt2img") # variationsand img2img jobs are not valid
                and jobs[job]["images_checked"] == True): # if the job has been checked
                # make sure to not queue txt2imgVariations jobs for images that have been already queued
                already_queued = False
                for otherjob in jobs:
                    if (jobs[otherjob]["starting_img"] == image and jobs[otherjob]["job_type"]=="txt2imgVariations"):
                        print(f"Variations for {image} already exist!")
                        already_queued = True
                        continue
                # if not already_queued : print(f"queueing {image}...")
                queue_txt2imgVariations(image)
    #  return jobIDs

def queue_txt2imgVariationsFromTask(taskID : str):
    """### Queue a txt2imgVariations task for each output in a txt2img task."""
    jobs = get_jobs_from_json()
    task = jobs[taskID]
    images = task["output_images"]
    if task["status"] != "done":
        print("Task is not done yet.")
        return
    if task["images_checked"] == True:
        jobIDs = []
        for image in images:
            jobIDs.append(queue_txt2imgVariations(original_image_path=f"{stableDiffusionDir}{image}"))
        return jobIDs
    else:
        print("Task images have not been checked yet.")
        return

def get_job_info(job_id) -> dict:
    """### Get the information of a task by its ID"""
    url = default_endpoint + f"/agent-scheduler/v1/task/{job_id}"
    response = requests.get(url)
    # print(response.json())
    return response.json()

def get_job_status(job_id: str) -> str:
    """Gets the status of a task by its ID"""
    job_info = get_job_info(job_id)
    try:
        job_status = job_info['data']['status']
    except KeyError:
        job_status = "error"
    return job_status

def get_output_images(job_id : str) -> list[str]:
    """Gets the output images of a job by its ID"""
    job_info = get_job_info(job_id)
    jobs = get_jobs_from_json()

    # if the task has failed, notify the user
    # TODO: maybe remove it from list?
    try :
        if job_info['data']['status'] == "failed":
            print(f"task {job_id} failed. returning nothing.")
            return []
    except KeyError:
        # remove the job from the json file if it has failed
        remove_job_from_json(job_id)
        return []


    # if the job has been checked, the images dir from the task info will not match with their actual location.
    # therefore, we get the images from the jobs.json file, if they are there, and verify that their path still exists.
    # if the path does not exist, we remove it from the list of images.
    try : 
        if jobs[job_id]["images_checked"] == True:
            images = jobs[job_id]["output_images"]
            images = [image for image in images if os.path.exists(f"{stableDiffusionDir}{image}")]
            return images
    except KeyError:
        pass

    # if the task has not been checked, we get the images from the task info.
    try :
        images = json.loads(job_info['data']['result'])['images']
    except TypeError: 
        images = None # return None if there are no images
    if images is not None:
        # remove all images containing the string "grid" in their name. remove all the images that are not actually there anymore.
        images = [image for image in images if "grid" not in image and os.path.exists(f"{stableDiffusionDir}{image}")]
    
    if images == []: # if the images from the job info have no paths, try to get them from the json and see if it works
        try:
            images = jobs[job_id]["output_images"]
            images = [image for image in images if os.path.exists(f"{stableDiffusionDir}{image}")]
        except KeyError:
            pass
    return images

def resume_queue():
    """Resumes a job by its ID"""
    url = default_endpoint + f"/agent-scheduler/v1/queue/resume"
    response = requests.post(url)
    return response.json()

def pause_queue():
    """Pauses the queue"""
    url = default_endpoint + f"/agent-scheduler/v1/queue/pause"
    response = requests.post(url)
    return response.json()

def remove_all_ended_jobs():
    """Removes jobs that fall into one of the following categories : 
    - failed
    - img2img that have been checked"""
    # update_all_jobs_in_json()
    jobs = get_jobs_from_json() 
    images_to_delete = []
    #TODO: remove the txt2img and txt2imgVariations jobs that have been checked and were part of an img2img or failed job.
    # there must be a "way back" to its original txt2img job and the generated image that led to the img2img.
    # TODO : in the rare edgecase there isn't, should just trim the generation tree up until the latest point

    # for each img2img job that has been marked as checked :
    img2img_jobs = [job for job in jobs if jobs[job]["job_type"] == "img2img"]
    #1. start from the img2img job
    for img2img_job in img2img_jobs:
        print("----------------------------------------")
        print(f"Checking {img2img_job}...")
        currentjob = img2img_job
        currentjob_type = "img2img"
        while currentjob_type != "txt2img":
            #2. get its starting img
            starting_image = jobs[currentjob]["starting_img"]
            images_to_delete.append(starting_image)
            print(f"Starting image : {starting_image}")
            #2.5 get the job associated with the starting img
            originaljob = ""
            for job in jobs:
                job_output_images = [output_image for output_image in jobs[job]["output_images"]]
                for image in job_output_images:
                    if starting_image == image:
                        originaljob = job
                        print(f"Original job : {originaljob}")
            if originaljob == "" : 
                print("Original job not found. Interrupting.")
                break

            jobs[originaljob]["output_images"].remove(starting_image) #remove the image from the jobs outputs
            #3. get the starting img's job type and remember the starting img
            currentjob_type = jobs[originaljob]["job_type"]
            currentjob = originaljob
            #4. if the job type is not a txt2img, redo from point 2

    #5. delete all the starting imgs up until the txt2img one from the checked_images folder.
    # TODO : add code to actually delete images. for safety reasons, we print them now
    print(images_to_delete)
    # for image in images_to_delete:
    #     os.remove(f"{stableDiffusionDir}{image}")

    # dump the jobs to the json file
    with open("jobs.json", "w") as file:
        json.dump(jobs, file, indent=4)

    # the function should leave usual jobs without any image outputs, a condition which gets taken care of by the update function.
