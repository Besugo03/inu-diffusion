# InuDiffusion
### An Automatic1111 Wrapper centered around batch processing

InuDiffusion is the over-engineered solution to my wish for better handling of batch images by stable diffusion, based around the principles of : 
- **traceability**
- **efficiency**
- **task-centric approach** (instead of single-image centric)

Having a pretty average GPU, i felt like handling my usual workflow was a bit of a waste of time since i had to wait for each image to finish in order to get some decent results, and keeping track of which images were variations of another, or good enough to upscale, or destined to be deleted, was a huge waste of time.

**please keep in mind that this project has been specifically targeted to my own workflow and needs, so it's not guaranteed it will be ideal for yours aswell.**

## Features :
- Keep track of each image's job status, generation parameters, originating image (in case it's a variation of another image or an img2img)