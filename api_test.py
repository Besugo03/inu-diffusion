import requests
import ImageLoadingSaving as ils

address = "http://127.0.0.1:5000"


# #  =============== TXT2IMG TEST ===============
# data = {
#     "prompt" : "",
#     "negative_prompt" : "",
#     "numJobs": 1,
# }

# response = requests.post(f"{address}/txt2img", json=data)
# print(response)

# =============== GLOBAL UPSCALE TEST ===============
response = requests.post(f"{address}/upscaleAllJobs")
print(response)

# =============== JOB UPSCALE TEST ===============
# data = {
#     "job" : "1746374772.588482"
# }
# response = requests.post(f"{address}/upscaleJob", json = data)
# print(response)

# =============== IMAGE UPSCALE TEST ===============
# data = {
#     "init_images" : ["1746398687.779045-2.png"]
# }

# =============== COUPLE JOB ===============
# data = {
#     "prompt" : "1girl, solo",
#     "negative_prompt" : "",
#     "numJobs" : 5
# }

# response = requests.post(f"{address}/txt2imgCouple", json=data)
# print(response)