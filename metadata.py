import os
from PIL import Image, PngImagePlugin

def copy_metadata(source_folder, target_folder):
    for filename in os.listdir(source_folder):
        source_path = os.path.join(source_folder, filename)
        # the target path has images saved as jpg, so we need to change the extension
        original_target_path = os.path.join(target_folder, filename)
        target_path = os.path.join(target_folder, filename.replace('.png', '.jpg'))

        if filename.endswith('.png'):
            try:
                # Open the source image and extract metadata
                source_image = Image.open(source_path)
                metadata = PngImagePlugin.PngInfo()

                for key, value in source_image.info.items():
                    metadata.add_text(key, str(value))

                # Open the target image
                target_image = Image.open(target_path)

                # Save the target image with the source metadata
                target_image.save(original_target_path, "png", pnginfo=metadata)

                print(f"Copied metadata from {source_path} to {target_path}")
            except Exception as e:
                print(f"Error copying metadata from {source_path} to {target_path}: {e}")

source_folder = 'C:\\Users\\alexp\\Downloads\\processed\\metadata'
target_folder = 'C:\\Users\\alexp\\Downloads\\processed'

# copy_metadata(source_folder, target_folder)

from typing import Tuple

def extract_prompt(image_path) -> Tuple[str, str]:
    """Extracts the prompt and negative prompt from the metadata of an image"""
    try:
        image = Image.open(image_path)
        metadata = image.info
        # print(metadata["parameters"])
        # everything before "Negative prompt:" is the prompt
        prompt = metadata["parameters"].split("Negative prompt:")[0]
        # remove any \n
        prompt = prompt.replace("\n", "")
        # everythin after "Negative prompt:" and before "Steps:" is the negative prompt
        negative_prompt = metadata["parameters"].split("Negative prompt:")[1].split("Steps:")[0]
        # remove any \n
        negative_prompt = negative_prompt.replace("\n", "")
        print(f"Prompt: {prompt}", f"Negative prompt: {negative_prompt}")
        return(prompt, negative_prompt)
    except Exception as e:
        print(f"Error extracting metadata from {image_path}: {e}")

def extract_seed(image_path) -> int:
    """Extracts the seed from the metadata of an image"""
    try:
        image = Image.open(image_path)
        metadata = image.info
        # seed is found in the substring  Seed: x, 
        seed = int(metadata["parameters"].split("Seed: ")[1].split(",")[0])
        print(f"Seed: {seed}")
        return seed
    except Exception as e:
        print(f"Error extracting metadata from {image_path}: {e}")

def reduce_lora_strength(prompt:str, lora_decrease_factor) -> str:
    """Reduces the strength of the LoRA prompt in the metadata"""
    # the Lora is formatted <lora:LORA_NAME:STRENGTH> so we need to find the strength and reduce it
    # there can be zero or multiple Lora prompts in the metadata
    
    if prompt.find("<lora:") == -1:
        return prompt
    
    lora_prompts = prompt.split("<lora:")
    reduced_prompt = ""
    reduced_prompt += lora_prompts[0]
    lora_prompts.pop(0)

    for lora_prompt in lora_prompts:
        second_split = lora_prompt.split(":")
        lora_strength = second_split[1].split(">")[0]
        reduced_strength = float(lora_strength) * lora_decrease_factor
        # round to 2 decimal places
        reduced_strength = round(reduced_strength, 2)
        reduced_prompt += f"<lora:{second_split[0]}:{reduced_strength}>"
        reduced_prompt += second_split[1].split(">")[1]

    print(f"Reduced LoRA strength: {reduced_prompt}")
    return reduced_prompt


# Example usage
# reduce_lora_strength("score_9,score_8_up,score_7_up, source_anime, <lora:BlushySpicy_Style_Pony-000003:0.7> <lora:style_norza_ponyXL-GLoRA:0.5> <lora:AsuraV2:0.4> rating_explicit,1girl, 1boy, from behind, spitroast, clothed sex,  <lora:Alya_SHFR_PonyXL-10:0.7> alya_def, alya_fanart, school uniform, red bowtie, open jacket, black skirt, pleated skirt, white thighhighs, hair ribbon, pink ribbon,", 0.5)