import requests
import ImageLoadingSaving as ils # Assuming this is used elsewhere or can be removed if not needed for this specific test block

address = "http://127.0.0.1:5000"

#  =============== START GENERATION WORKER ===============
print("\\n=============== START GENERATION WORKER ===============")
response_start_worker = requests.post(f"{address}/start-generation-worker")
print("Response from /start-generation-worker:")
try:
    print(response_start_worker.json())
except requests.exceptions.JSONDecodeError:
    print(f"Error decoding JSON. Status code: {response_start_worker.status_code}, Response text: {response_start_worker.text}")
print("==========================================================")


#  =============== TXT2IMG MULTI-RESOLUTION TEST ===============

# print("\\n=============== TXT2IMG TEST ===============")

# data_multi_res = {
#     "prompt" : "1girl, red hair, red eyes, mature woman, looking at viewer, dress",
#     "negative_prompt" : "",
#     "cfg_scale" : 7,
#     "numJobs": 10, # Should match the number of resolutions in the list
#     "steps": 25 # Optional: specify steps
# }

# response_multi_res = requests.post(f"{address}/txt2img", json=data_multi_res)
# print("Response from /txt2img (multi-resolution):")
# try:
#     print(response_multi_res.json())
# except requests.exceptions.JSONDecodeError:
#     print(f"Error decoding JSON. Status code: {response_multi_res.status_code}, Response text: {response_multi_res.text}")
# print("==========================================================")

#  =============== FORGE GENERATION TEST ===============
print("\\n=============== FORGE COUPLE GENERATION TEST ===============")

# This test targets the /txt2imgCouple endpoint which uses the ForgeCoupleJob type.
forge_couple_data = {
    "prompt": """
    1boy, 1girl, male focus, !hachiouji naoto, brown hair, glasses, shy, !otoko_no_ko, !male_penetrated, full body, ass, small penis, rape, {!anal fingering | anal, }, small penis humiliation,
    NEXT 1boy, 1girl, femdom, !nagatoro hayase, !?smug, !femdom, !laughing, !strapon, dildo,
    NEXT femdom, 1boy, 1girl, male penetrated, otoko_no_ko, 
    """,
    "negative_prompt": "hetero, futanari, faceless male",
    "numJobs": 13,
    "steps": 25, 
    "cfg_scale": 5,
    "global_effect": "Last Line",
    # "styles" : [],

    # Width and height are omitted to use the default SDXL resolutions in the API
}

response_forge_couple = requests.post(f"{address}/txt2imgCouple", json=forge_couple_data)
print("Response from /txt2imgCouple (Forge Generation):")
try:
    print(response_forge_couple.json())
except requests.exceptions.JSONDecodeError:
    print(f"Error decoding JSON. Status code: {response_forge_couple.status_code}, Response text: {response_forge_couple.text}")
print("==========================================================")
