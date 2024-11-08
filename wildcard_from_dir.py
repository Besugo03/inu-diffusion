import os
import json
import safetensorsMetadata

default_lora_weight = 0.7
stableDiffusionDir = "/mnt/Lexar 2TB/stable-diffusion-webui-forge"

# Ask user for LoRa weight
# if not specified, use default.
lora_weight = input(f"please specify the default weight for lora (default = {default_lora_weight}) : ")
lora_weight = lora_weight if lora_weight else default_lora_weight
print(f"lora weight is [ {lora_weight} ]")

lora_directory = stableDiffusionDir+"/models/Lora"
wildcard_dir = "/".join(lora_directory.split("/")[:-2]) + "/extensions/sd-dynamic-prompts/wildcards"

# Ask user to choose a directory from which to extract the Lora
subdirectories = os.listdir(lora_directory)
for subdir_idx in range(len(subdirectories)):
    print(f"{subdir_idx+1}. {subdirectories[subdir_idx]}")

chosen_directory = int(input("Please choose a directory to extract Lora from: "))
print(f"Chosen directory is {subdirectories[chosen_directory-1]}")

# then, list the files(wildcards) in the chosen directory
wildcards = os.listdir(wildcard_dir)
print("Wildcards:")
for wildcard_idx in range(len(wildcards)):
    print(f"{wildcard_idx+1}. {wildcards[wildcard_idx]}")

# ask the user to either put the index of the wildcard file they want to add to, or create a new one by typing the name of the new file.
chosen_wildcard = input("Please choose a wildcard file to add to: ")
if chosen_wildcard.isdigit():
    wildcard_name = wildcards[int(chosen_wildcard)-1][:-4]
else:
    wildcard_name = chosen_wildcard




# extract only the .json files from the chosen directory and put them in a list
json_files = [f for f in os.listdir(lora_directory+f"/{subdirectories[chosen_directory-1]}") if f.endswith('.json')]
# extract the list of pony models from the directory (end with .safetensors)
pony_loras = safetensorsMetadata.get_pony_loras_from_dir(lora_directory+f"/{subdirectories[chosen_directory-1]}", verbose=True)

# for each json file, filter out the ones that are not pony models
json_pony_files = [x for x in json_files if x[:-5]+".safetensors" in pony_loras]

lora_and_activation_list = []

added_files = 0

try : 
    with open (wildcard_dir+f"/{wildcard_name}.txt", 'r') as f:
        old_lora_file = f.readlines()
        f.close()
except FileNotFoundError:
    print("No wildcard file found. Creating a new one...")
    old_lora_file = []

for json_file_idx in range(len(json_pony_files)):
    with open (lora_directory+f"/{subdirectories[chosen_directory-1]}/{json_files[json_file_idx]}", 'r') as f:
        data = json.load(f)
        activation_text = data["activation text"]
        
        # check if the activation text is already in the wildcard file. If it is, skip it.
        file_added = True
        for line in old_lora_file:
            if (json_files[json_file_idx])[:-5] in line:
                print(f"Skipping {json_files[json_file_idx]}... (already in wildcard file)")
                file_added = False
                continue
        if file_added: 
            added_files += 1
            print(f"Adding {json_files[json_file_idx]} to the wildcard file...")
        
        # if the activation text contains the string ", ,", it means that there are multiple options for the activation text.
        # in this case, add a line formatted as {<lora:filename:weight> option1 | <lora:filename:weight> option2 | ...}
        if ", ," in activation_text:
            # newString = ""
            activation_options = activation_text.split(", ,")
            activation_text = activation_options[0]
            # print(activation_options[0])
            # for option_idx in range(len(activation_options)):
            #     if option_idx == 0:
            #         newString += "{" + f"<lora:{(json_files[json_file_idx])[:-5]}:{lora_weight}> {activation_options[option_idx]} |"
            #     elif option_idx == len(activation_options)-1:
            #         newString += f"<lora:{(json_files[json_file_idx])[:-5]}:{lora_weight}> {activation_options[option_idx]}" + "}"
            #     else:
            #         newString += f"<lora:{(json_files[json_file_idx])[:-5]}:{lora_weight}> {activation_options[option_idx]} |"
            # lora_and_activation_list.append(newString)
        # else:
        lora_and_activation = f"<lora:{(json_files[json_file_idx])[:-5]}:{lora_weight}> {activation_text},"
        if file_added : lora_and_activation_list.append(lora_and_activation)
        f.close()

# for elem in lora_and_activation_list:
#     print(elem)

# write the list to a file, in which each line is an element of the list.

print(lora_and_activation_list)

# add the new lora and activation text to the old wildcard file
with open (wildcard_dir+f"/{wildcard_name}.txt", 'a') as f:
    for elem in lora_and_activation_list:
        f.write(elem + "\n")
    f.close()

print("Done. Added a total of", added_files, "files to the wildcard file.")