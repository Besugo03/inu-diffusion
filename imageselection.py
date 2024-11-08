import os
from PIL import Image, ImageTk
import tkinter as tk
import json
import jobsManager
import b64encoder as encoder

jobsManager.default_endpoint = "http://127.0.0.1:7860"

jobs = jobsManager.get_jobs_from_json() # get the jobs

for job_ID in jobs:
    # if jobs[job_ID]["images_checked"] == False:
        jobsManager.update_job_in_json(job_ID, jobs[job_ID]["job_type"], jobs[job_ID]["starting_img"]) # update each one

jobs = jobsManager.get_jobs_from_json() # re-get the jobs after updating them

# create the images list
images_list = []
for job_ID in jobs:
    if jobs[job_ID]["images_checked"] == False:
        images_list.append(jobs[job_ID]["output_images"])
print("IMAGES LIST : ")
print(images_list)
images = [image for sublist in images_list for image in sublist]
print("IMAGES : ")
print(images)

def display_images():
    global jobs
    global images
    directory = "/mnt/Lexar 2TB/stable-diffusion-webui-forge/"

    if not jobs:
        print(f"Jobs.json is empty.")
        return

    if not images:
        print(f"No images left to check!")
        return

    root = tk.Tk()
    root.geometry("800x600")  # Set the window size

    image_index = 0
    current_image = None

    # Function to display the next image
    def display_next_image():
        nonlocal image_index, current_image
        if image_index < len(images):
            if current_image:
                current_image.destroy()
            image_path = os.path.join(directory, images[image_index])
            img = Image.open(image_path)
            img.thumbnail((800, 600))  # Resize the image to fit the window
            photo = ImageTk.PhotoImage(img)
            current_image = tk.Label(root, image=photo)
            current_image.image = photo  # Keep a reference to the image
            current_image.pack()
            image_index += 1
        else:
            root.destroy()

    # Function to handle 'y' key press
    def on_yes_press(event):
        print(f"Key {event.char} pressed: Moving to next image")
        display_next_image()

    # Function to handle 'n' key press (delete)
    def on_no_press(event):
        if image_index > 0:
            image_to_delete = images[image_index - 1]
            # os.remove(os.path.join(directory, image_to_delete))
            # instead of deleting the image, move it to a different folder called "to_delete"
            to_delete_dir = f"{directory}output/to_delete"
            if not os.path.exists(to_delete_dir):
                os.makedirs(to_delete_dir)
            imageName = image_to_delete.split('/')[-1]
            os.rename(f"{directory}{image_to_delete}", f"{to_delete_dir}/{imageName}")
            # print(f"Deleted {image_to_delete}")
            print(f"{imageName} marked for deletion")
            display_next_image()

    # Bind the 'y' and 'n' keys to their respective functions
    root.bind('y', on_yes_press)
    root.bind('n', on_no_press)

    display_next_image()
    root.mainloop()




display_images()

# re-update the available images in the jobs.json file
for job_ID in jobs:
    if jobs[job_ID]["images_checked"] == False:
        jobsManager.update_job_in_json(job_ID, jobs[job_ID]["job_type"], jobs[job_ID]["starting_img"])

# once done, set all the jobs "images_checked" property to True, for all the successfully displayed images.
with open("jobs.json", "r") as file:
    jobs = json.load(file)
    for job_ID in jobs:
        if jobs[job_ID]["output_images"] is not None and jobs[job_ID]["status"] == "done":
            jobs[job_ID]["images_checked"] = True
            

            # Move images to the checked_images folder
            for image in jobs[job_ID]["output_images"]:
                txt2img_checked_dir = f"/mnt/Lexar 2TB/stable-diffusion-webui-forge/output/txt2img-images/checked_images"
                img2img_checked_dir = f"/mnt/Lexar 2TB/stable-diffusion-webui-forge/output/img2img-images/checked_images"
                if not os.path.exists(txt2img_checked_dir):
                    os.makedirs(txt2img_checked_dir)
                if not os.path.exists(img2img_checked_dir):
                    os.makedirs(img2img_checked_dir)
                
                if "txt2img" in jobs[job_ID]["job_type"]:
                    checked_dir = txt2img_checked_dir
                elif "img2img" in jobs[job_ID]["job_type"]:
                    checked_dir = img2img_checked_dir
                
                imageIndex = jobs[job_ID]["output_images"].index(image)
                if jobs[job_ID]["job_type"] == "txt2img": # if the job type is txt2img:
                    oldImageName = image.split('/')[-1]
                    # imageIndex = position of the image in the list of output images
                    newImageName = f"{encoder.uuid_to_base64(job_ID)}@{imageIndex}.png"
                else : # if the job type is img2img or txt2txtVariations:
                    startingimageName = jobs[job_ID]["starting_img"].split('/')[-1]
                    startingimageName_nopng = startingimageName.split('.')[0]
                    newImageName = f"{startingimageName_nopng}_{imageIndex}.png"


                os.rename(f"/mnt/Lexar 2TB/stable-diffusion-webui-forge/{image}", 
                          f"{checked_dir}/{newImageName}")

                # Update job JSON with new paths
                for i in range(len(jobs[job_ID]["output_images"])): # for each image in the job's output images
                    if jobs[job_ID]["output_images"][i] == image: # if the image is the one that was moved
                        if "txt2img" in jobs[job_ID]["job_type"]:
                            jobs[job_ID]["output_images"][i] = f"output/txt2img-images/checked_images/{newImageName}"
                        elif "img2img" in jobs[job_ID]["job_type"]:
                            jobs[job_ID]["output_images"][i] = f"output/img2img-images/checked_images/{newImageName}"
                    if jobs[job_ID]["starting_img"] == image: # if the image is the starting image
                        jobs[job_ID]["starting_img"] = f"output/txt2img-images/checked_images/{newImageName}"
                # same with img2img

with open("jobs.json", "w") as file:
    json.dump(jobs, file, indent=4)
file.close()