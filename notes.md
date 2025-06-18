
**MUST REMOVE NECESSARY DEFAULTS.JSON FILE, HAVE TO CREATE IT ON FIRST BOOT OR PUSH A DEFAULT ONE.**

*New dock for moving between pages* : https://ui.aceternity.com/components/floating-dock

*Main generation tab* : 
- txt2img
  - Lora autocomplete
  - Lora wildcard autocomplete
  - Would be nice to have the loras have a modal/popover to see the image preview. Helps imagine the future image instead of having to scroll and search for the lora amongs lots.
  - Potential tree-like, per-tag wildcard expansion (?)
- txt2img Forge option (checkbox probably)
- getting current processing job (at a time interval)
  - under image, show the image's metadata or at least the tags that were used (in case of wildtags)
- shortcut to process focused/current wildTags
- defaults loading/setting
  - multiple defaults (?)
- style selection
- lora dir generator

Gelbooru query : https://gelbooru.com//index.php?page=dapi&s=post&q=index&tags=hatsune_miku%20-tail&json=1

*Jobs global view tab* : 
- Queued/completed jobs overview
  - Upscale chosen images
  - Upscale all images
  - Upscale whole job
  - Delete images
  - modify and/or retry a job
  - mouse-over zoom for easier image inspection / image-by-image view (?) : https://ui.aceternity.com/components/lens
  - Quick approve/delete image section
    - Must keep which jobs have been checked somewhere.
- Maybe use the Expandable Cards component to view imageas better with a proper carousel (?) :  https://ui.aceternity.com/components/expandable-card

*Research/prompt generation tab* :
  - Get trending characters
  - Browse some danbooru images for recreating
    - Bar under each one to tell how well-tagged the image is
    - Recreate image, which obviously has a better effect with more well-tagged images
    - have a text input on top which automatically appends that stuff to the end of the prompt (to specify characters / environments / whatever wants to be substituted)
- Danbooru exclusive :
  - boy/girl character classification
  - Fetching characters relevant to a tag
    - Also be able to filter by boy/girl
  - Fetching posts relevant to a tag
  - Get currently popular tags
  - Get currently popular characters
- Image Recreator (from Gelbooru tag) 
  - To implement danbooru for the same 
  - To implement DeepBooru interrogation to enrich image tags
    - Should have an option to either use local model or remotely hosted ones like on huggingface
- Get trending characters for both danbooru and gelbooru



- Wildcard processing : 
  - Processing wildcards without extension (POSTPONED)

- Things to implement :
  - Potential support for more extensions 
  x Saving defaults for generation
    - Scheduler

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
