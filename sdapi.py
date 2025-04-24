from flask import Flask, request, jsonify
import subprocess

from SDGenerator_worker import Txt2ImgJob, ForgeCoupleJob, startGeneration
import JobQueuer
import defaultsHandler

app = Flask(__name__)

@app.route('/txt2img', methods=['POST'])
def txt2img():
    data = request.get_json()
    print(f"got txt2img job '{data['prompt']}'...")

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

    generator = JobQueuer.JobGenerator(job=generationJob, prompts=[data["prompt"]], resolutionList=resolutionList, numJobs=data["numJobs"])
    generatedjobs = generator.makeJobs()
    JobQueuer.saveJobs(generatedjobs)

    return jsonify(data)

@app.route('/txt2imgCouple', methods=['POST'])
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

    generator = JobQueuer.JobGenerator(job=generationJob, prompts=[data["prompt"]], resolutionList=resolutionList, numJobs=data["numJobs"])
    generatedjobs = generator.makeJobs()
    JobQueuer.saveJobs(generatedjobs)

    return jsonify(data)

@app.route('/upscale', methods=['POST'])
def img2img():
    from SDGenerator_worker import UpscaleJob
    import ImageLoadingSaving as ils
    from imageMetadata import getImageMetadata
    data = request.get_json()

    givenImageb64 = ils.encode_file_to_base64(data["init_images"][0])

    image_metadata = getImageMetadata(data["init_images"][0])
    print("metadata : ",image_metadata)
    resolution = image_metadata[image_metadata.find("Size: ") + 6: image_metadata.find(", Model hash:")].split("x")
    seed = image_metadata[image_metadata.find("Seed: ") + 6: image_metadata.find(", Size:")]
    sampler = image_metadata[image_metadata.find("Sampler: ") + 9: image_metadata.find(", Schedule type:")]
    prompt = image_metadata[0:image_metadata.find("Negative prompt:")]
    negative_prompt = image_metadata[image_metadata.find("Negative prompt: ") + 17:image_metadata.find("Steps:")]
    
    defaults = defaultsHandler.loadDefaultsFromFile("defaults.json")

    generationJob = UpscaleJob(
        prompt = prompt,
        negative_prompt = data.get("negative_prompt", negative_prompt),
        styles = data.get("styles", []),
        seed = data.get("seed", seed),
        batch_size = 1 ,
        cfg_scale = data.get("cfg_scale", 5),
        steps = data.get("steps", 25),
        width = int(resolution[0])*2,
        height = int(resolution[1])*2,
        sampler = data.get("sampler", sampler),
        enable_hr = data.get("enable_hr", False),
        hr_scale = data.get("hr_scale", 2),
        hr_upscaler = data.get("hr_upscaler", "2xHFA2kAVCSRFormer_light"),
        denoising_strength = data.get("denoising_strength", 0.4),
        init_images = [givenImageb64],
        metadata = image_metadata,
        infotext= "test"
    )

    width = data.get("width", None)
    height = data.get("height", None)
    if width is None or height is None:
        resolutionList = [(width, height)]
    else:
        resolutionList = [(width, height)]

    generator = JobQueuer.JobGenerator(job=generationJob, prompts=[prompt], resolutionList=[(int(resolution[0])*2,int(resolution[1])*2)], numJobs=data["numJobs"])
    generatedjobs = generator.makeJobs()
    JobQueuer.saveJobs(generatedjobs)

    return jsonify(data)

@app.route('/saveDefaults', methods=['POST'])
def saveDefaults():
    data = request.get_json()
    defaultsHandler.saveDefaultsToFile(data, "defaults.json")
    return jsonify({"status": "success"})


if __name__ == "__main__":
    import tag_filterer as tf
    tf.forbiddenTags = defaultsHandler.loadDefaultsFromFile("defaults.json")["forbidden_tags"]
    subprocess.Popen(["./venv/Scripts/python.exe", "SDGenerator_worker.py"])
    # Run the Flask app
    app.run()