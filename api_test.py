import jobsManager as jm

jm.default_endpoint = "http://127.0.0.1:7860/"

print(jm.test_txt2img(prompt="rating_safe, 1girl, pov, makima \(chainsaw man\),", sampler_name="DPM++ 2M SDE", styles=["New-clean style 3"], n_iter=1))
