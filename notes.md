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

- Wildcard processing :
  - Processing wildcards
  - Caching bangtags/characters

- Things to implement :
  - Queueing with all these different things in mind
  - doing some A1111 requests structure research to include extensions and things like ADetailer / Extras etc...
  - Saving defaults for generation
    - Sampler
    - Scheduler
    - Steps
    - Resolution / multiple resolution to choose randomly
    - CFG
    - Batch count
    - Style selected from csv

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