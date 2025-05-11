import requests
import urllib.parse

BASE_URL = "http://127.0.0.1:7860"
LORA_NAME_RAW = ""

# Single encoding (standard)
encoded_once = urllib.parse.quote(LORA_NAME_RAW)
# Double encoding
encoded_twice = urllib.parse.quote(encoded_once)

url_single_encoded = f"{BASE_URL}/tacapi/v1/lora-info/{encoded_once}"
url_double_encoded = f"{BASE_URL}/tacapi/v1/lora-info/{encoded_twice}"

print(f"Testing single encoding: {url_single_encoded}")
# Make request with url_single_encoded ...
print(requests.get(url_single_encoded).json())

print(f"Testing double encoding: {url_double_encoded}")
print(requests.get(url_double_encoded).json())
# Make request with url_double_encoded ...
# (You can adapt the previous script's get_lora_info function)