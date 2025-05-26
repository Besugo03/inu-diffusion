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

# #  =============== MEMORY TEST ===============
# set the memory first to avoid slow inference
# testdatamemory = {"forge_inference_memory": 4000}
# success = False
# while not success:
#     try :
#         requests.post(f"{address}/sdapi/v1/options", json=testdatamemory)
#         success = True
#         print("[INFO] Memory set successfully.")
#     except Exception as e:
#         print(f"Error setting memory: {str(e)}")
#         # wait for 1 second before retrying
#         import time
#         time.sleep(1)
#         pass

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

#  =============== JOB SKIP TEST ===============

# data = {
#     "jobID" : "1748004674.078294",
# }
# response = requests.post(f"{address}/skipJob", json=data)
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


# =============== IMAGE RETRIEVAL TEST ===============

# data = {
#     "jobID" : "1748117801.678689",
#     # "thumbnail" : True,
# }
# response = requests.post(f"{address}/jobImages", json = data)
# print(response.json())

# =============== REDIRECTION TEST ===============


# response = requests.get(f"{address}/sdapi/v1/sd-models")
# print(response.json())

# models = response.json()
# for model in models:


# def generateLoraWildcard(wildcardDir : str, strength : float = 0.7):
#     response = requests.get(f"{address}/sdapi/v1/loras")
#     print(response.json())

#     loras = response.json()
#     # results = []
#     finalString = "{ "
#     for lora in loras:
#         print(lora['name'])
#         if lora['path'].replace("\\", "/").split("/Lora/")[1].startswith(wildcardDir) == False:
#             print(f"[INFO] Lora {lora['name']} not in the wildcard directory. Skipping...")
#             continue
#         try :
#             training_tags_folders = lora['metadata']['ss_tag_frequency']
#         except KeyError:
#             print("[INFO] KeyError: ss_tag_frequency not found in metadata for lora " + lora['name'])
#             continue
            

#         finalString += f" <lora:{lora['name']}:{strength}> " 
#         # foundTags = []
#         for folder in training_tags_folders:
#             finalString += " {  "
#             sorted_tags = sorted(training_tags_folders[folder].items(), key=lambda x: x[1], reverse=True)

#             # get the tags that, starting from the top, make x% of the total dataset tag frequency
#             def get_tags_by_percentage(tags, percentage):
#                 tags_sum = sum(tag[1] for tag in tags)
#                 threshold = tags_sum * (percentage / 100)
#                 current_sum = 0
#                 selected_tags = []
#                 for tag in tags:
#                     current_sum += tag[1]
#                     selected_tags.append(tag[0])
#                     if current_sum >= threshold:
#                         break
#                 return selected_tags
            
#             selected_tags = get_tags_by_percentage(sorted_tags, 20)
#             # print(selected_tags)
#             # foundTags.append({folder : selected_tags})
#             # print(foundTags)
#             for tag in selected_tags:
#                 finalString += f"{tag}, "
#             finalString = finalString[:-2] + " | "
#             finalString = finalString[:-2] + " }"
#         # results.append({lora['name'] : foundTags})
#         finalString += " | "
#     return finalString[:-3] + " }"

# print(generateLoraWildcard("Positions"))

# response = requests.post(f"{address}/txt2imgCouple", json=data)
# print(response)