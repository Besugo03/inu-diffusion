import concurrent.futures
import time
import requests
import re
import popular_characters_utils
import json
import datetime
import wildcard_cache as cache
import tag_filterer


# TODO : Fix an issue where if the tag is part of a dynamic prompt eg. {!test | test2} it will not be read and replaced correctly as its missing both the comma and the endline

def nearest_tags(input_tag):
    url = f"https://danbooru.donmai.us/tags.json?search[name_matches]={input_tag}*&limit=100"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    # Sort tags by post_count in descending order
    sorted_tags = sorted(data, key=lambda tag: tag['post_count'], reverse=True)
    
    # Extract the names of sorted tags
    matching_tags = [tag['name'] for tag in sorted_tags]
    return matching_tags

def fetch_related_tags(tag):
    url = f"https://danbooru.donmai.us/related_tag.json?query={tag}&limit=1000"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data['related_tags']  # This gives tags related to the specified query

def get_relevant_tags(tag, include_characters=False):
    forbiddenCategories = [1, 5, 3]
    if not include_characters:
        forbiddenCategories.append(4)
    apiTags = fetch_related_tags(tag)

    # if apiTags == [] it probably means the tag was not written correctly.
    # in that case, we will try to find the nearest tag to the input tag
    if apiTags == []:
        # print(f"Tag {tag} not found...")
        tag = nearest_tags(tag)
        if tag == []:
            # print("No similar tags found. Exiting...")
            return []
        else:
            tag = tag[0]
        print(f"Assuming you ment '{tag}'. Proceeding with this tag...")
        apiTags = fetch_related_tags(tag)

    # TODO : put some actual forbidden tags here, possibly to include in the filtering .py file
    apiTags = [tag for tag in apiTags if "censor" not in tag['tag']['name'] and "monochrome" not in tag['tag']['name']]

    # sort the tags by jaccard similarity
    jaccard_tags = sorted(apiTags,key=lambda x: x['jaccard_similarity'], reverse=True)
    jaccard_tags = [tag['tag']['name'] for tag in jaccard_tags if tag['tag']['category'] not in forbiddenCategories]
    jaccard_tags = jaccard_tags[1:30]

    # sort the tags by cosine similarity
    cosine_tags = sorted(apiTags, key=lambda x: x['cosine_similarity'], reverse=True)
    cosine_tags = [tag['tag']['name'] for tag in cosine_tags if tag['tag']['category'] not in forbiddenCategories]
    cosine_tags = cosine_tags[1:30]

    # sort the tags by overlap coefficient
    overlap_tags = sorted(apiTags, key=lambda x: x['overlap_coefficient'], reverse=True)
    overlap_tags = [tag['tag']['name'] for tag in overlap_tags if tag['tag']['category'] not in forbiddenCategories]
    overlap_tags = overlap_tags[1:30]

    # merge the tags while removing duplicates and keeping the order
    # NOTE : as of now overlap tags are not used, but they can be added in the future.
    final_tags = list(dict.fromkeys(jaccard_tags + cosine_tags))
    final_tags = tag_filterer.filter_tags(final_tags)
    return final_tags

def list_to_wildcard(tagList : list, num_tags : int) -> str:
    """Generates a wildcard tag for the given list of tags, written in the standard Sd-dynamic prompts format
    (e.g. {tag1|tag2|tag3})...."""
    wildcard = "{"
    wildcard += f"{num_tags}$$"
    for tag in tagList:
        wildcard += f"{tag}|"
    wildcard = wildcard[:-1] + "}"
    print(len(tagList))
    if len(tagList) <= 1:
        return ""
    return wildcard

def process_bangtag(input_tag, num_tags):
    related_tags = get_relevant_tags(input_tag)
    bangTag = list_to_wildcard(related_tags, num_tags)
    return bangTag

def parallel_fetch_uncommon_tags(
        input_tag : str, 
        num_tags : int, 
        tag_cap : int, 
        return_wildcard : bool = False,
        max_workers : int =25, 
        delay : float = 0.1) -> list:
    # query the related tags endpoint with the tag
    related_tags_endpoint = f"https://danbooru.donmai.us/related_tag.json?query={input_tag}&limit=1000"
    response = requests.get(related_tags_endpoint).json()

    # first, we will get the tags associated with the input tag
    related_tags = [tag['tag']['name'] for tag in response['related_tags'] if tag['tag']['category'] == 0]
    related_tags = tag_filterer.filter_tags(related_tags)
    print(len(related_tags))
    # remove all the tags that have a color in them (they are probably hair/eye colors)
    # related_tags = [tag for tag in related_tags if not any(color in tag for color in forbidden_terms)]
    with open("related_tags.json", "w") as f:
        json.dump(related_tags, f)
        f.close()
    far_tags = related_tags[150:250]
    print(f"Far tags: {far_tags}")
    # log the related tags for debugging to a json
    with open("trimmed_related_tags.json", "w") as f:
        json.dump(far_tags, f)
        f.close()

    def fetch_tag_data(tag):
        search = f"{tag}%20{input_tag}"
        print(f"Searching for tag {search}".replace("%20", " "))
        response = requests.get(f"https://danbooru.donmai.us/posts.json?tags={search}&limit=200")
        if response.status_code == 200:
            try:
                scores = response.json()
                scores = [post['score'] for post in scores]
                if scores:
                    average_score = sum(scores) / len(scores)
                    max_score = max(scores)
                else:
                    average_score = 0
                    max_score = 0
            except requests.exceptions.JSONDecodeError:
                print(f"Error decoding JSON for tag {search}")
                average_score = 0
                max_score = 0
        else:
            print(f"Error fetching data for tag {search}: {response.status_code}")
            average_score = 0
            max_score = 0
        print(f"Average score: {average_score}, Max score: {max_score}")
        return tag, (average_score, max_score)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for tag in far_tags:
            futures.append(executor.submit(fetch_tag_data, tag))
            time.sleep(delay)  # Add delay between requests

        results = [future.result() for future in concurrent.futures.as_completed(futures)]

    far_tags_data = dict(results)
    # for each tag, also add its position in the list from the related tags
    far_tags_data = {tag: (far_tags.index(tag), far_tags_data[tag][0], far_tags_data[tag][1]) for tag in far_tags_data}
    print("Far tags data:")
    print(far_tags_data)
    for tag in far_tags_data:
        # calculate the "niche score" for each tag
        # farther tags will have a higher niche score
        # it is also influenced by the average and max scores
        # we use the log function to make the niche score more pronounced
        # the log function will increase the value of the niche score, but it will also make the difference between the scores more pronounced
        # this is because the log function is not linear, but logarithmic
        import math
        niche_score = math.log(far_tags_data[tag][0] + 1) * (far_tags_data[tag][1] + far_tags_data[tag][2])
        far_tags_data[tag] = (niche_score, far_tags_data[tag][1], far_tags_data[tag][2])
    sorted_tags_niche = sorted(far_tags_data.items(), key=lambda x: x[1][0], reverse=True)
    tags = [tag[0] for tag in sorted_tags_niche][:tag_cap]
    if return_wildcard:
        wildcard = "{"
        wildcard += f"{num_tags}$$"
        for tag in tags:
            wildcard += f"{tag} | "
        wildcard = wildcard[:-3] + "}"
        return wildcard if len(tags) > 0 else ""
    else:
        return tags

def process_wildcard_prompt(prompt):
    """given a prompt, it finds the instant wildcard syntax (eg. 1girl,1boy,!requestedTag:numberoftags, othertags...) and replaces it with the
    generated wildcard tags and the requested number of wildcard tags (written as {numberoftags$$tag1|tag2|tag3...})"""
    
    new_prompt = ""
    # split_tags = re.split(r',|{|}|\||]\n', prompt)
    split_tags = re.split(r'(,|[\{\}\|\]])', prompt)
    print(split_tags)
    for tag_segment in split_tags:
        if tag_segment == None or tag_segment == " " or tag_segment == "" or tag_segment == ",":  # Skip empty segments
            continue
        if tag_segment == tag_segment == "{" or tag_segment == "}" or tag_segment == "|":
            new_prompt += tag_segment
            continue
        stripped_tag = tag_segment.strip()
        print(f"stripped_tag: {stripped_tag} | tag_segment: {tag_segment}")
        # just check the first 4 characters of the tag to see if it's a bangtag or a varietytag (the modifiers are alwyas at the start)
        if "?" in tag_segment[:4] or "!" in tag_segment[:4]:
            # if there is a ":" in the tag and the last character is a number, then it's a tag with a number of tags
            if ":" in tag_segment and tag_segment.strip()[-1].isdigit():
                print("tag has a number of tags specified")
                # grab the position of the last ":" NOT THE FIRST, since the tag can have multiple colons (eg. tags like :P or :) )
                last_colon = stripped_tag.rfind(":")
                num_tags = stripped_tag[last_colon+1:]
                stripped_tag = stripped_tag[:last_colon]
                num_tags = int(num_tags)
            else:
                stripped_tag = stripped_tag
                num_tags = 1
            if stripped_tag[0] == "-":
                stripped_tag = stripped_tag[1:]
            else : new_prompt += stripped_tag.strip("!?&").replace("\\","") + ","
            only_tag = stripped_tag.strip("!?&").replace("\\","")
            bangTag = ""
            varietyTag = ""

            if "!" in stripped_tag: # if it's a bangtag
                relevant_tags = cache.queryForWildTag(only_tag, "bang", num_tags)
                if relevant_tags == None:
                    relevant_tags = get_relevant_tags(only_tag)
                    # save the bangTag in the cache with an expiration time of 1 week
                    cache.saveWildTag(only_tag, "bang", relevant_tags, datetime.datetime.now().timestamp() + 604800)
                relevant_tags = tag_filterer.filter_tags(relevant_tags)
                bangTag = list_to_wildcard(relevant_tags, num_tags)

            if "?" in stripped_tag[:4]: # if it's a varietyTag
                varietyTag = cache.queryForWildTag(only_tag, "variety", num_tags)
                if varietyTag == None:
                    varietyTag = parallel_fetch_uncommon_tags(only_tag, num_tags, 20, return_wildcard=False)
                    # save the varietyTag in the cache with an expiration time of 1 week
                    cache.saveWildTag(only_tag, "variety", varietyTag, datetime.datetime.now().timestamp() + 604800)
                varietyTag = tag_filterer.filter_tags(varietyTag)
                varietyTag = list_to_wildcard(varietyTag, num_tags)

            if "&" in tag_segment[:4]:
                new_prompt += bangTag + ","
                new_prompt += varietyTag
            else:
                if (bangTag and not varietyTag) or (varietyTag and not bangTag):
                    new_prompt += bangTag + varietyTag
                else:
                    new_prompt += "{ " + bangTag + " | " + varietyTag + " }, "

        else :
            new_prompt += stripped_tag + ","

    return new_prompt