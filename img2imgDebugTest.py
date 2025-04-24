import base64
import json
import ImageLoadingSaving

imagelocation = "test.png"
# b64image = base64.b64encode(open(imagelocation, "rb").read()).decode("utf-8")
b64image = ImageLoadingSaving.encode_file_to_base64(imagelocation)


payload = {
    "prompt": "",
    "negative_prompt": "",
    "seed": -1,
    "batch_size": 1,
    "steps": 25,
    "cfg_scale": 5,
    "width": 896,
    "height": 1152,
    "sampler": "Euler",
    "save_images": True,
    "metadata" : "testunoduetrequattro",
    "denoising_strength": 0.4,
    "init_images": [
        b64image
    ]
}

import requests
response = requests.post("http://127.0.0.1:7860/sdapi/v1/img2img", json=payload)
print(response.json())