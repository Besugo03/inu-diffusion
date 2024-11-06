import requests

# TODO : Fix an issue where if the tag is part of a dynamic prompt eg. {!test | test2} it will not be read and replaced correctly as its missing both the comma and the endline

def nearest_tag(input_tag):
    url = f"https://danbooru.donmai.us/tags.json?search[name_matches]={input_tag}*&limit=100"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    # Sort tags by post_count in descending order
    sorted_tags = sorted(data, key=lambda tag: tag['post_count'], reverse=True)
    
    # Extract the names of sorted tags
    matching_tags = [tag['name'] for tag in sorted_tags]
    return matching_tags

def get_api_related_tags(tag):
    url = f"https://danbooru.donmai.us/related_tag.json?query={tag}&limit=1000"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data['related_tags']  # This gives tags related to the specified query

# print("Directly fetched related tags:", related_tags)
def get_relevant_tags(tag):
    forbiddenCategories = [1, 5, 3, 4]
    forbiddenTags = ["loli", "shota", "guro", "gore", "scat", "furry", "bestiality","lolidom"]
    apiTags = get_api_related_tags(tag)

    # if apiTags == [] it probably means the tag was not written correctly.
    # in that case, we will try to find the nearest tag to the input tag
    if apiTags == []:
        # print(f"Tag {tag} not found...")
        tag = nearest_tag(tag)
        if tag == []:
            # print("No similar tags found. Exiting...")
            return []
        else:
            tag = tag[0]
        print(f"Assuming you ment '{tag}'. Proceeding with this tag...")
        apiTags = get_api_related_tags(tag)

    apiTags = [tag for tag in apiTags if "censored" not in tag['tag']['name'] and "monochrome" not in tag['tag']['name']]

    # sort the tags by jaccard similarity
    jaccard_tags = sorted(apiTags,key=lambda x: x['jaccard_similarity'], reverse=True)
    jaccard_tags = [tag['tag']['name'] for tag in jaccard_tags if tag['tag']['name'] not in forbiddenTags and tag['tag']['category'] not in forbiddenCategories]

    jaccard_tags = jaccard_tags[1:25]


    # sort the tags by cosine similarity
    cosine_tags = sorted(apiTags, key=lambda x: x['cosine_similarity'], reverse=True)
    cosine_tags = [tag['tag']['name'] for tag in cosine_tags if tag['tag']['name'] not in forbiddenTags and tag['tag']['category'] not in forbiddenCategories]

    cosine_tags = cosine_tags[1:25]


    # sort the tags by overlap coefficient
    overlap_tags = sorted(apiTags, key=lambda x: x['overlap_coefficient'], reverse=True)
    overlap_tags = [tag['tag']['name'] for tag in overlap_tags if tag['tag']['name'] not in forbiddenTags and tag['tag']['category'] not in forbiddenCategories]

    overlap_tags = overlap_tags[1:25]

    # merge the tags while removing duplicates and keeping the order
    final_tags = list(dict.fromkeys(jaccard_tags + cosine_tags))
    return final_tags

def generate_instant_wildcard(tagList):
    """Generates a wildcard tag for the given list of tags, written in the standard Sd-dynamic prompts format
    (e.g. {tag1|tag2|tag3})...."""
    wildcard = "{"
    for tag in tagList:
        wildcard += f"{tag}|"
    wildcard = wildcard[:-1] + "}"
    return wildcard

def process_instant_wildcard_prompt(prompt):
    """given a prompt, it finds the instant wildcard syntax (eg. 1girl,1boy,!requestedTag:numberoftags, othertags...) and replaces it with the
    generated wildcard tag and the requested number of wildcard tags (written as {numberoftags$$tag1|tag2|tag3...})"""
    # if the number is not specified (: is not present) then we will assume the user wants 3 tags
    
    import re
    # find the instant wildcard syntax, which is basically either tags between an ! and an , or tags between an ! and the end of the string
    # we need to do this for all the tags in the prompt
    
    # for each match, if the : is not present, we will assume the user wants 1 tag
    # else, we will extract the number of tags the user wants
    matches = re.findall(r'!(.*?)(?:,|$)', prompt)
    for match in matches:
        if ":" in match:
            tag, num_tags = match.split(":")
            num_tags = int(num_tags)
        else:
            tag = match
            num_tags = 1
        print(f"Tag: {tag}, Number of tags: {num_tags}")
        related_tags = get_relevant_tags(tag)
        # print("Related tags:", related_tags)
        wildcard = generate_instant_wildcard(related_tags)
        if wildcard == "}":
            print(f"Tag {tag} not found. Skipping...")
            # remove the match from the prompt and everything thats after it but before ,
            wholematch = f"!{match},"
            prompt = prompt.replace(wholematch, "")
            continue
        wildcard = tag + ", {" + f"{num_tags}$$" + wildcard[1:]
        print("Generated wildcard:", wildcard)
        print("\n")
        if ":" in match:
            prompt = prompt.replace(f"!{tag}:{num_tags}", wildcard)
        else:
            prompt = prompt.replace(f"!{tag}", wildcard)
    return prompt