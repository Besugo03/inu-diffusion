def getImageMetadata(imagePath : str) -> str:
    from PIL import Image
    img = Image.open(imagePath)
    metadata = img.info
    Prompt = metadata['parameters']
    return Prompt