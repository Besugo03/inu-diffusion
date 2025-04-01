
# all of the below tags are used to filter out tags that are not allowed.
# these include any tag that CONTAINS any of the words in the list.
colors = ["aqua","black","blue","brown","green","grey","orange","purple","pink","red","white","yellow","amber","girl","boy"]
forbiddenTags = ["loli", "shota", "guro", "gore", "scat", "furry", "bestiality","lolidom","artist","text","official","futa_","futanari","censor"]

def filter_tags(original_tags : list) -> list:
    """
    Function that filters out tags that contain any of the words in the colors and forbiddenTags list.
    This also applies to any tag that CONTAINS any of the words in the lists.
    """
    filtered_tags = []
    for tag in original_tags:
        if any(color in tag for color in colors) or any(forbidden in tag for forbidden in forbiddenTags):
            continue
        else: 
            filtered_tags.append(tag)
    return filtered_tags