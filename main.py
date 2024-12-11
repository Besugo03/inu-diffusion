from fastapi import FastAPI, Request
import jobsManager as jm
import httpx
import requests

app = FastAPI()

sdBaseUrl = "http://127.0.0.1:7860"
jm.default_endpoint = sdBaseUrl

@app.get("/")
async def root():
    # make a request to stable diffusion api for a sample image (txt2img)
    image = jm.test_txt2img(prompt="rating_safe, 1girl, pov, makima \(chainsaw man\),", sampler_name="DPM++ 2M SDE", styles=["New-clean style 3"], n_iter=1)
    # return the image to the user
    return image

# try to call the service
# @app.get("/test_txt2img")
# async def test_txt2img(prompt: str, sampler_name: str, styles: list, n_iter: int):
#     async with httpx.AsyncClient() as client:
#         response = await client.get(f"{service_url}/test_txt2img", params={"prompt": prompt, "sampler_name": sampler_name, "styles": styles, "n_iter": n_iter})
#         return response.json()
