Functions for the app the api provides :

- Image Recreator (from Gelbooru tag) 
  - To implement danbooru for the same 
  - To implement DeepBooru interrogation to enrich image tags
    - Should have an option to either use local model or remotely hosted ones like on huggingface
- Get trending characters for both danbooru and gelbooru
- lora dir generator

- Danbooru exclusive :
  - boy/girl character classification
  - Fetching characters relevant to a tag
    - Also be able to filter by boy/girl
  - Fetching posts relevant to a tag
  - Get currently popular tags
  - Get currently popular characters

- Wildcard processing : (POSTPONED)
  - Processing wildcards without extension

- Things to implement :
  - Potential support for more extensions 
  x Saving defaults for generation
    - Scheduler

Things the frontend should include :
- Normal image generation interface like stable diffusion
  - Txt2Img
  - wildcard processing on-generation
  - wildcard instant-expand
  - Lora autocomplete instant-expand
  - Lora directory wildcard generation and autocomplete
  - Potential interface for tree-like prompt-wildcard generation where you expand a single tag and then choose some to expand it into
  - both text and visual input
  - LoraNado-like lora randomization

- Queued/completed jobs overview
  - Upscale chosen images
  - modify and retry a job
  - mouse-over zoom for easier image inspection / image-by-image view

- Research/prompt generation tab
  - Get trending characters
  - Browse some danbooru images for recreating
    - Bar under each one to tell how well-tagged the image is
    - Recreate image, which obviously has a better effect with more well-tagged images
    - have a text input on top which automatically appends that stuff to the end of the prompt (to specify characters / environments / whatever wants to be substituted)


Endpoints necessari : 
T ottenere i jobs
- interrogate image recreator ==POSTPONED==
/ generate lora wildcard


http://127.0.0.1:7860/sdapi/v1/options
  "sd_model_checkpoint": "unholyDesireMixSinister_v40_1477760.safetensors",
  "sd_vae": "sdxl_vae.safetensors",
  "interrogate_deepbooru_score_threshold": 0.7,

http://127.0.0.1:7860/sdapi/v1/sd-models
http://127.0.0.1:7860/sdapi/v1/refresh-checkpoints
http://127.0.0.1:7860/sdapi/v1/refresh-loras
