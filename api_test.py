import requests
import ImageLoadingSaving as ils

address = "http://127.0.0.1:5000"


# #  =============== TXT2IMG TEST ===============
# data = {
#     "prompt" : "",
#     "negative_prompt" : "",
#     "cfg_scale" : 7,
#     "numJobs": 10,
# }

# response = requests.post(f"{address}/txt2img", json=data)
# print(response)

# =============== GLOBAL UPSCALE TEST ===============
# data = {
#     "denoising_strength" : 0.4
# }

# response = requests.post(f"{address}/upscaleAllJobs", json=data)
# print(response)

# =============== JOB UPSCALE TEST ===============
# data = {
#     "job" : "1746640206.199103"
# }
# response = requests.post(f"{address}/upscaleJob", json = data)
# print(response)

# =============== IMAGE UPSCALE TEST ===============
# data = {
#     "init_images" : ["1746640206.199103-1.png"]
# }

# response = requests.post(f"{address}/upscaleTask", json=data)
# print(response)

# =============== COUPLE JOB ===============
# data = {
#     "prompt" : "1girl, solo",
#     "negative_prompt" : "",
#     "numJobs" : 5
# }

# response = requests.post(f"{address}/txt2imgCouple", json=data)
# print(response)