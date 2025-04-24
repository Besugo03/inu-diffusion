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

def encode_file_to_base64(path):
    import base64
    with open(path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')