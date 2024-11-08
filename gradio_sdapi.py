import gradio as gr
import api_test_sd as api
import time

stableDiffusionDir = "/mnt/Lexar 2TB/stable-diffusion-webui-forge"

imageChoices = []

# Function to generate images by calling the API
def generate_images(prompt, negative_prompt, n_iter):
    # Call your API to generate images (replace with the actual API call)
    job_id = api.queue_txt2img(prompt=prompt, negative_prompt=negative_prompt, n_iter=n_iter)
    return job_id

# Function to update checkboxes dynamically
def generate_and_update(prompt, negative_prompt, n_iter):
    try:
        images_job_id = generate_images(prompt, negative_prompt, n_iter)  # get the job ID for the images
        
        # Wait for the images to be generated
        print("Status :")
        print(api.get_task_status(images_job_id))
        while api.get_task_status(images_job_id) != "done":
            print(api.get_task_info(images_job_id))
            time.sleep(1)  # Sleep to avoid excessive polling
        
        # Fetch the generated image directories
        imageDirs = api.get_output_images(images_job_id)  # get the image dirs
        print(imageDirs)
        
        # Convert the relative paths to absolute paths
        imagesAbsolutePaths = [f"{stableDiffusionDir}/{imageDir}" for imageDir in imageDirs if "grid" not in imageDir]
        
        # Return the image paths directly to Gradio Gallery
        return imagesAbsolutePaths

    except Exception as e:
        # In case of any failure, log the error (and optionally return an error message)
        print(f"Error: {str(e)}")
        return [], []  # Return empty lists if something goes wrong

def update_checkboxes(gallery):
    print(gallery)
    imageChoices = [image for image in gallery if "grid" not in image]
    return gr.CheckboxGroup(imageChoices, label="updated", interactive=True)


# Gradio interface
with gr.Blocks() as ui:
    
    with gr.Row():
        # Input fields for prompt, negative prompt, and number of images
        prompt_input = gr.Textbox(lines=3, label="Prompt")
        negative_prompt_input = gr.Textbox(lines=3, label="Negative Prompt")
        n_iter_input = gr.Number(label="Number of images to generate", interactive=True, maximum=10, minimum=1, value=2)
        generate_button = gr.Button("Generate Images")
    
    with gr.Row():
        # Gallery to display generated images
        image_gallery = gr.Gallery(label="Generated Images",interactive=False, )

    checkboxes = gr.CheckboxGroup(label="Choose images to save", choices=[])
    # Link the button click event to generating images and updating the checkbox group
    generate_button.click(
        fn=generate_and_update,  # This function handles both image generation and checkbox updating
        inputs=[prompt_input, negative_prompt_input, n_iter_input],  # Inputs for the function
        outputs=[image_gallery]  # Outputs: images go to the gallery, labels go to the checkboxes
    )
    image_gallery.change(
        fn = update_checkboxes,
        inputs = image_gallery,
        outputs = checkboxes
    )

# Launch the Gradio app
ui.launch(allowed_paths=[stableDiffusionDir])