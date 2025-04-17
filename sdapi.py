from typing import Literal
import requests
import instant_wildcard as iw

address = "127.0.0.1:7860"

# generic class which will be used to handle the requests.
# it contains the endpoint to which the request will be sent,
# the payload which will be sent in the request, and the method
# which will be used to send the request.
class Txt2ImgJob:

    endpoint = str

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
        # TODO Change the endpoint to the one which is used in the script
        endpoint = f"http://{address}/sdapi/v1/txt2img"
        payload = job.to_dict()
        response = requests.post(endpoint, json=payload)
        return response

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

basePrompt = ""

promptList = [
    basePrompt + "",
]

generator = JobGenerator(testcouplejob, promptList,[(1024,1024),(1152,896),(896,1152),(1216,832),(832,1216),(1344,768),(768,1344)], 5)
testJobsList = generator.makeJobs()
for i in testJobsList:
    print(i.to_dict())

# set the memory first to avoid slow inference
testdatamemory = {"forge_inference_memory": 5000}

requests.post(f"http://{address}/sdapi/v1/options", json=testdatamemory)

for i in testJobsList:
    response = handler.send_job(i)
    print(response.json())