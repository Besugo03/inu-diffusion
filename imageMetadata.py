def getImageMetadata(imagePath : str) -> str:
    from PIL import Image
    import ast
    img = Image.open(imagePath)
    metadata = img.info
    parameters = metadata['parameters']
    # convert parameters to dict
    parameters = ast.literal_eval(parameters)
    return parameters