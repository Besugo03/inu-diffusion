import datetime
import json
from typing import Literal

# from instant_wildcard import get_relevant_tags, process_varietytag


def saveWildTag(tag, tag_type, expanded_tags, expiration):
    """
    Function that saves the expanded tags for a tag in the cache.
    """
    # structure for the json cache file : { "tag" : { "bang" : { "tags" : "tags", "expiration" : "expiration_date"}, "variety" : { "tags" : "tags", "expiration" : "expiration_date"} } }
    try:
        with open("tag_cache.json", "r", encoding="utf-8") as f:
            cache = json.load(f)
            f.close()
    except FileNotFoundError:
        cache = {}
    except json.JSONDecodeError:
        cache = {}
    
    if tag not in cache:
        cache[tag] = {}
    cache[tag][tag_type] = {"tags" : expanded_tags, "expiration" : expiration}
    with open("tag_cache.json", "w") as f:
        json.dump(cache, f)
        f.close()

def queryForWildTag(tag : str, tag_type : Literal["bang","variety"], num_tags : int) -> list | None:
    """
    Function that manages tags caching for the instant wildcard generation.
    **tag_type** is either "bang" or "variety"
    If a tag is cached, and is not expired, it will be returned.
    If a tag is not cached, it will return None.
    """
    # structure for the json cache file : { "tag" : { "bang" : { "tags" : "tags", "expiration" : "expiration_date"}, "variety" : { "tags" : "tags", "expiration" : "expiration_date"} } }
    try:
        with open("tag_cache.json", "r", encoding="utf-8") as f:
            cache = json.load(f)
            f.close()
    except FileNotFoundError:
        cache = {}
    except json.JSONDecodeError:
        cache = {}
    
    if tag in cache:
        if tag_type in cache[tag]:
            print(f"Tag {tag} found in cache.")
            if cache[tag][tag_type]["expiration"] > datetime.datetime.now().timestamp():
                print(f"Tag {tag} is not expired. Checking if the number of tags saved is enough...")
                # TODO : implement a system where, in case the number of tags is not enough, the function will call the corresponding function to get more tags
                cached_tags = cache[tag][tag_type]["tags"]
                return cached_tags
    return None
        # # if any of the conditions above are not met, then the tag is not cached or is expired, 
        # # so we will call the corresponding function, get the tags, cache them and the time and return them.
        # print(f"Tag {tag} not found in cache. Proceeding to generate the wildcard...")
        # if tag_type == "bang":
        #     tags = get_relevant_tags(tag)
        #     print(f"bangtag for {tag} generated, saving it in the cache...")
        #     if tag not in cache:
        #         cache[tag] = {}
        #     # save the tags in the cache
        #     cache[tag]["bang"] = {"tags" : tags, "expiration" : datetime.datetime.now().timestamp() + 604800}
        #     # the expiration time is 1 week (604800 seconds)
        #     with open("tag_cache.json", "w") as f:
        #         json.dump(cache, f)
        #         f.close()
        #     return "{" + str(num_tags) + "$$" + "|".join(tags) + "}"
        # if tag_type == "variety":
        #     tags = process_varietytag(tag, 1, return_tags=True)
        #     print(f"varietytag for {tag} generated, saving it in the cache...")
        #     if tag not in cache:
        #         cache[tag] = {}
        #     # save the tags in the cache
        #     cache[tag]["variety"] = {"tags" : tags, "expiration" : datetime.datetime.now().timestamp() + 604800}
        #     # the expiration time is 1 week (604800 seconds)
        #     with open("tag_cache.json", "w") as f:
        #         json.dump(cache, f)
        #         f.close()
        #     return "{" + str(num_tags) + "$$" + "|".join(tags) + "}"