import json
import base64
import metadata
import PIL
from PIL import Image
import requests
import os

# handles the scheduling of jobs.

# json is formatted the following way:
# { "job_ID" : { "job_type" : job_type, "status" : status, "starting_img" : starting_image_dir } }
# }
# job type is either "txt2img", "txt2imgVariations", "img2img"
# status is either pending, done, or failed.
# starting_img is the directory of the image that started the job.

default_endpoint = str
stableDiffusionDir = "/mnt/KingstonSSD/stable-diffusion-webui-forge/"

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
    
    jobs[job_ID] = {
        "job_type" : job_type if job_type is not None else jobs[job_ID]["job_type"],
        "status" : get_job_status(job_ID),
        "starting_img" : None if (job_type == "txt2img") else starting_img_path,
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

def remove_job_from_json(job_ID):
    """### Remove a job from the jobs.json file."""
    with open("jobs.json", "r") as file:
        jobs = json.load(file)
    jobs.pop(job_ID)
    with open("jobs.json", "w") as file:
        json.dump(jobs, file)

def queue_img2img(
        image_path=None,
        width=None, height=None,
        # tiling=True, # to check if tiling is actually vae or something else
        denoising_strength = 0.35,
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
    print(f"txt2img job started with ID {response.json()["task_id"]}")
    update_job_in_json(response.json()["task_id"], "txt2img")
    return response.json()["task_id"]

def queue_txt2imgVariations(
        original_image_path = None,
        n_iter = 3,
        prompt_addon = "",
        negative_prompt_addon = "",
        width = 1024 , height = 1024,
        cfg_scale = 5,
):
    # open the image and get the prompt and negative prompt
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