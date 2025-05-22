import requests
import ImageLoadingSaving as ils

address = "http://127.0.0.1:5000"

# #  =============== WORKER TEST ===============
response = requests.post(f"{address}/start-generation-worker")
print(response.json())

# response = requests.get(f"{address}/worker-status")
# print(response.json())

# response = requests.post(f"{address}/stop-generation-worker")
# print(response.json())

# #  =============== TXT2IMG TEST ===============
# TODO there is no logging for errors like missing the prompt or negative prompt
# data = {
#     "prompt" : "",
#     "negative_prompt" : "",
#     "cfg_scale" : 7,
#     "numJobs": 10,
# }

# response = requests.post(f"{address}/txt2img", json=data)
# print(response.json())

#  =============== JOB DELETE TEST ===============
# data = {
#     "jobID" : "1747939831.398353",
# }
# response = requests.post(f"{address}/deleteJob", json=data)
# print(response.json())


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

# =============== REDIRECTION TEST ===============

# response = requests.get(f"{address}/sdapi/v1/sd-models")
# print(response.json())

# models = response.json()
# for model in models:

# response = requests.get(f"{address}/sdapi/v1/loras")
# print(response.json())

# numero problematico : 39

# lora = response.json()
# print(lora[39]['name'])
# print(lora[39]['path'].replace("\\", "/").split("/Lora/")[1])
# training_tags_folders = lora[39]['metadata']['ss_tag_frequency']
    
# foundTags = []
# for folder in training_tags_folders:
#     sorted_tags = sorted(training_tags_folders[folder].items(), key=lambda x: x[1], reverse=True)
#     tags_sum = sum([tag[1] for tag in sorted_tags])
#     # print(sorted_tags)
#     # print(tags_sum)

#     # get the tags that, starting from the top, make x% of the total dataset tag frequency
#     def get_tags_by_percentage(tags, percentage):
#         tags_sum = sum(tag[1] for tag in tags)
#         threshold = tags_sum * (percentage / 100)
#         current_sum = 0
#         selected_tags = []
#         for tag in tags:
#             current_sum += tag[1]
#             selected_tags.append(tag[0])
#             if current_sum >= threshold:
#                 break
#         return selected_tags
    
#     selected_tags = get_tags_by_percentage(sorted_tags, 20)
#     # print(selected_tags)
#     foundTags.append({folder : selected_tags})
# print(foundTags)

# response = requests.post(f"{address}/txt2imgCouple", json=data)
# print(response)