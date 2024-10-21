from PIL import Image

image = "D:/SD-Forge retry/stable-diffusion-webui-forge/output/txt2img-images/2024-06-05/00000-3411611621.png"

img = Image.open(image)
metadata = img.info
### the prompt is the first string before the first \n
# print(metadata)
Prompt = metadata['parameters']
print(Prompt)