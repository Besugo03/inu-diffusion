import requests

def get_related_tags_directly(tag):
    url = f"https://danbooru.donmai.us/related_tag.json?query={tag}&limit=1000"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data['related_tags']  # This gives tags related to the specified query

# Example usage
main_tag = "gun"
related_tags = get_related_tags_directly(main_tag)
# print("Directly fetched related tags:", related_tags)
forbiddenCategories = [1, 5, 3]

forbiddenTags = ["loli", "shota", "guro", "gore", "scat", "furry", "bestiality","lolidom"]

# sort the tags by jaccard similarity
jaccard_tags = sorted(related_tags,key=lambda x: x['jaccard_similarity'], reverse=True)
jaccard_tags = [tag['tag']['name'] for tag in jaccard_tags if tag['tag']['name'] not in forbiddenTags and tag['tag']['category'] not in forbiddenCategories]

jaccard_tags = jaccard_tags[1:25]


# sort the tags by cosine similarity
cosine_tags = sorted(related_tags, key=lambda x: x['cosine_similarity'], reverse=True)
cosine_tags = [tag['tag']['name'] for tag in cosine_tags if tag['tag']['name'] not in forbiddenTags and tag['tag']['category'] not in forbiddenCategories]

cosine_tags = cosine_tags[1:25]


# sort the tags by overlap coefficient
overlap_tags = sorted(related_tags, key=lambda x: x['overlap_coefficient'], reverse=True)
overlap_tags = [tag['tag']['name'] for tag in overlap_tags if tag['tag']['name'] not in forbiddenTags and tag['tag']['category'] not in forbiddenCategories]

overlap_tags = overlap_tags[1:25]

# merge the tags while removing duplicates and keeping the order
final_tags = list(dict.fromkeys(jaccard_tags + cosine_tags))

print("Final tags:", final_tags)
print(len(final_tags))
