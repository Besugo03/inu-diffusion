def encode_image(image):
    """
    Encode an image to base64 string.

    :param image: PIL Image object or path to an image

    :return: base64 encoded string
    """
    from io import BytesIO
    import base64
    from PIL import Image
    
    if isinstance(image, str):
        image = Image.open(image)
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

def decode_image(img_str):
    """
    Decode a base64 string to PIL Image object.
    :param img_str: base64 encoded string
    :return: PIL Image object
    """
    import base64
    from io import BytesIO
    from PIL import Image
    img_data = base64.b64decode(img_str)
    image = Image.open(BytesIO(img_data))
    return image

def save_image(image, filename):
    """
    Save a PIL Image object to a file.
    :param image: PIL Image object
    :param filename: path to save the image
    """
    image.save(filename)

def encode_file_to_base64(path, thumbnail=False):
    import base64
    from PIL import Image
    from io import BytesIO
    with open(path, 'rb') as file:
        # if thumbnail, return a downsized version of the image
        if thumbnail:
            img = Image.open(file)
            img.thumbnail((256, 256))
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            buffer.seek(0)
            return base64.b64encode(buffer.read()).decode('utf-8')
        return base64.b64encode(file.read()).decode('utf-8')
    
def add_metadata_to_image(imagepath : str, metadata : dict):
    """
    Add metadata to a PIL Image object.
    :param image: PIL Image object
    :param metadata: metadata to add
    """
    from PIL import Image
    from PIL import PngImagePlugin
    img = Image.open(imagepath)
    meta = PngImagePlugin.PngInfo()
    for key, value in metadata.items():
        meta.add_text(key, str(value))
    img.save(imagepath, pnginfo=meta)

