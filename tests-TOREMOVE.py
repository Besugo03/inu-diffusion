import requests
import re
from fuzzywuzzy import fuzz

def wildcardFromTagGroup(tag_group : str, return_array : bool) -> str|list:
    """
    Given a correct tag group from the Danbooru wiki (eg. "Gestures") it will generate a wildcard string
    made up of all the tags in that group.
    """
    test_endpoint = "https://danbooru.donmai.us/wiki_pages.json?search[title]=tag_group:"
    response = requests.get(test_endpoint+tag_group).json()

    responseBody = response[0]["body"]
    # match all the occurrences of links (delimited by [[ and ]])
    # and then extract the text between the brackets
    links = re.findall(r"\[\[(.*?)\]\]", responseBody)
    links = [link for link in links if "tag group" not in link.lower() and "tag_group" not in link.lower()]
    return "{"+"|".join(links)+"}"

groups = ["eyes_tags"]

for group in groups:
    print(wildcardFromTagGroup(group.lower(), False))
    print(",")