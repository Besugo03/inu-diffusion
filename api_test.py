import requests
import ImageLoadingSaving as ils

address = "http://127.0.0.1:5000"

data = {
    "prompt" : "1girl, solo",
    "negative_prompt" : "",
    "numJobs": 5,
}

response = requests.post(f"{address}/txt2img", json=data)
print(response)

# testImage = ils.encode_image("test.png")

# data = {
#     "init_images" : ["test.png"],
#     "numJobs" : 1
# }

# response = requests.post(f"{address}/upscale",json=data)