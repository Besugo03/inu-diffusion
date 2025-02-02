import requests
import re
import popular_characters_utils

# TODO : Fix an issue where if the tag is part of a dynamic prompt eg. {!test | test2} it will not be read and replaced correctly as its missing both the comma and the endline

forbidden_terms = ["aqua","black","blue","brown","green","grey","orange","purple","pink","red","white","yellow","amber","dark","girl","boy","artist","text","official","futa_","futanari","loli","censor"]

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
    jaccard_tags = [tag for tag in jaccard_tags if not any(color in tag for color in forbidden_terms)]

    jaccard_tags = jaccard_tags[1:25]


    # sort the tags by cosine similarity
    cosine_tags = sorted(apiTags, key=lambda x: x['cosine_similarity'], reverse=True)
    cosine_tags = [tag['tag']['name'] for tag in cosine_tags if tag['tag']['name'] not in forbiddenTags and tag['tag']['category'] not in forbiddenCategories]
    cosine_tags = [tag for tag in cosine_tags if not any(color in tag for color in forbidden_terms)]

    cosine_tags = cosine_tags[1:25]


    # sort the tags by overlap coefficient
    overlap_tags = sorted(apiTags, key=lambda x: x['overlap_coefficient'], reverse=True)
    overlap_tags = [tag['tag']['name'] for tag in overlap_tags if tag['tag']['name'] not in forbiddenTags and tag['tag']['category'] not in forbiddenCategories]
    overlap_tags = [tag for tag in overlap_tags if not any(color in tag for color in forbidden_terms)]

    overlap_tags = overlap_tags[1:25]

    # merge the tags while removing duplicates and keeping the order
    final_tags = list(dict.fromkeys(jaccard_tags + cosine_tags))
    return final_tags

def generate_instant_wildcard(tagList, num_tags):
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

def process_instant_wildcard_prompt(prompt):
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
            if ":" in tag_segment and tag_segment[-1].isdigit():
                # grab the position of the last ":" NOT THE FIRST, since the tag can have multiple colons (eg. tags like :P or :) )
                last_colon = stripped_tag.rfind(":")
                num_tags = stripped_tag[last_colon+1:]
                stripped_tag = stripped_tag[:last_colon]
                num_tags = int(num_tags)
                print(f"specified num_tags: {num_tags}")
            else:
                stripped_tag = stripped_tag
                num_tags = 1
            if stripped_tag[0] == "-":
                stripped_tag = stripped_tag[1:]
            else : new_prompt += stripped_tag.strip("!?&").replace("\\","") + ","
            print("\n")
            only_tag = stripped_tag.strip("!?&").replace("\\","")
            print(f"only_tag: {only_tag}")
            if "!" in stripped_tag: # if it's a bangtag
                related_tags = get_relevant_tags(only_tag)
                bangTag = generate_instant_wildcard(related_tags,num_tags)

            if "?" in stripped_tag[:4]: # if it's a varietyTag
                varietyTag = popular_characters_utils.parallel_fetch_uncommon_tags(only_tag, num_tags, 10) + ","

            if "&" in tag_segment[:4]:
                new_prompt += bangTag + ","
                new_prompt += varietyTag

            else:
                new_prompt += "{ " + bangTag + " | " + varietyTag + " }"

        else :
            new_prompt += stripped_tag + ","

    return new_prompt