from safetensors import safe_open
import os

# Path to your .safetensors file
def get_pony_loras_from_dir(
        dir: str,
        verbose: bool = False
) -> list[str]:
    """Returns a list of all .saftensors files in the given directory that have been trained on a pony model."""
    # all files in the main dir that end with .safetensors
    Loras = [f for f in os.listdir(dir) if f.endswith('.safetensors')]
    pony_models = []
    non_pony_models = []
    allowed_models_words = ["pony", "pdxl", "290640", "autism"]

    for lora in Loras:
        with safe_open(dir+f"/{lora}", 'pt') as f:
            metadata = f.metadata()
            if metadata:
                if "ss_sd_model_name" in metadata:
                    if verbose:
                        print(f"{lora} has been trained on: {metadata["ss_sd_model_name"]}")
                    if any(word in metadata["ss_sd_model_name"] for word in allowed_models_words):
                        if verbose:
                            print(f"{lora} has been trained on a pony model.")
                        pony_models.append(lora)
                else:
                    if verbose:
                        print(f"{lora} does not contain any relevant training metadata.")
                    non_pony_models.append(lora)
    print (f"Found {len(pony_models)} pony models and {len(non_pony_models)} non-pony models.")
    return pony_models