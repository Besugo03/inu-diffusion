import os
import requests
import concurrent.futures
import time

# Configuration
# api = rule34 or danbooru
API_CONFIG = {
    'api': 'danbooru',  # Change to 'danbooru' to use the Danbooru API
    'danbooru': {
        'base_url': 'https://danbooru.donmai.us',
        'username': 'bozog',  # Replace with your Danbooru username
        'api_key': 'V5iwdBa3fYjUKvN3QPh2jwx6'     # Replace with your Danbooru API key
    }
}

def fetch_images_metadata(tag, limit=200):
    """Fetches metadata for images based on a tag and limit."""
    if API_CONFIG['api'] == 'rule34':
        RULE34_API_URL = "https://api.rule34.xxx/index.php?page=dapi&s=post&q=index"
        params = {
            'tags': tag,
            'limit': limit,
            'json': 1
        }
        try:
            response = requests.get(RULE34_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, dict) and data.get('success') == 'false':
                print(f"Error: {data.get('message', 'Unknown error')}")
                return []
            return data
        except requests.RequestException as e:
            print(f"Error fetching data from Rule34 API: {e}")
            return []
    elif API_CONFIG['api'] == 'danbooru':
        return fetch_all_danbooru_posts(tag, limit)
    else:
        print("Unsupported API")
        return []

def fetch_all_danbooru_posts_by_tag(tag, limit=200):
    """Fetches posts from Danbooru for a given tag, circumventing the 200 results limit."""
    base_url = API_CONFIG['danbooru']['base_url']
    username = API_CONFIG['danbooru']['username']
    api_key = API_CONFIG['danbooru']['api_key']
    
    all_posts = []
    before_id = None

    fetched_images = 0

    while fetched_images < limit:
        params = {
            'login': username,
            'api_key': api_key,
            'tags': tag,
            'limit': limit
        }
        if before_id:
            params['page'] = f'b{before_id}'
        
        try:
            response = requests.get(f'{base_url}/posts.json', params=params)
            response.raise_for_status()
            posts = response.json()
            if not posts:
                break
            all_posts.extend(posts)
            before_id = posts[-1]['id']
            print(f"Fetched {len(posts)} posts, continuing from ID {before_id}")
        except requests.RequestException as e:
            print(f"Error fetching data from Danbooru API: {e}")
            break
        fetched_images += len(posts)

    return all_posts

def fetch_all_danbooru_posts(limit=1000):
    """Fetches all posts from Danbooru, circumventing the 200 results limit."""
    base_url = API_CONFIG['danbooru']['base_url']
    username = API_CONFIG['danbooru']['username']
    api_key = API_CONFIG['danbooru']['api_key']
    
    all_posts = []
    before_id = None

    fetched_images = 0

    while fetched_images < limit:
        params = {
            'login': username,
            'api_key': api_key,
            'limit': 200 if limit > 200 else limit
        }
        if before_id:
            params['page'] = f'b{before_id}'
        
        try:
            response = requests.get(f'{base_url}/posts.json', params=params)
            response.raise_for_status()
            posts = response.json()
            if not posts:
                break
            all_posts.extend(posts)
            before_id = posts[-1]['id']
            print(f"Fetched {len(posts)} posts, continuing from ID {before_id}")
        except requests.RequestException as e:
            print(f"Error fetching data from Danbooru API: {e}")
            break
        fetched_images += len(posts)

    return all_posts

# tests
# print(fetch_images_metadata('cat_ears', 10))

def get_popular_tags(limit=10):
    """Fetches the most popular tags from the API."""
    if API_CONFIG['api'] == 'rule34':
        RULE34_API_URL = "https://api.rule34.xxx/index.php?page=dapi&s=tag&q=index"
        params = {
            'order': 'count',
            'limit': limit
        }
        try:
            response = requests.get(RULE34_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return [tag['name'] for tag in data]
        except requests.RequestException as e:
            print(f"Error fetching data from Rule34 API: {e}")
            return []
    elif API_CONFIG['api'] == 'danbooru':
        return get_popular_danbooru_tags(limit)
    else:
        print("Unsupported API")
        return []
    
def get_popular_danbooru_tags(post_limit, tag_limit=10):
    """Fetches the most popular tags from Danbooru."""
    base_url = API_CONFIG['danbooru']['base_url']
    username = API_CONFIG['danbooru']['username']
    api_key = API_CONFIG['danbooru']['api_key']
    
    params = {
        'login': username,
        'api_key': api_key,
        'order': 'count',
        'limit': post_limit,
    }
    
    # It will fetch the most recent posts (defined by limit) and return the amount of times each tag has been used.
    # fetch the most recent posts
    try:
        posts = fetch_all_danbooru_posts(post_limit)
        print(f"Fetched {len(posts)} posts")
        tags = [tag for post in posts for tag in post['tag_string_character'].split()]
        # if the tag is not a character tag or a general tag, remove it.
        # to know this, we will send a request to the tags endpoint and check the category of the tag.
        # if the category is 0, it is a general tag. If it is 4, it is a character tag.
        tag_counts = {}
        for tag in tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        # print(tag_counts)
        # sort the tags by count in descending order
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_tags[:tag_limit]
    except requests.RequestException as e:
        print(f"Error fetching data from Danbooru API: {e}")
        return []
    
def get_weighted_popular_characters(post_limit=1000,limit=10, excluded_words=[]):
    """Fetches the most popular tags from the API and weights them based on the posts score."""
    if API_CONFIG['api'] == 'rule34':
        RULE34_API_URL = "https://api.rule34.xxx/index.php?page=dapi&s=tag&q=index"
        params = {
            'order': 'count',
            'limit': limit
        }
        try:
            response = requests.get(RULE34_API_URL, params=params)
            response.raise_for_status()
            data = response.json()
            return [tag['name'] for tag in data]
        except requests.RequestException as e:
            print(f"Error fetching data from Rule34 API: {e}")
            return []
    elif API_CONFIG['api'] == 'danbooru':
        posts = fetch_all_danbooru_posts(post_limit)
        # create a list with the tag as the key and the sum of the scores as the value
        tag_ratings = {}
        for post in posts:
            score = post['score']
            for tag in post['tag_string_character'].split():
                tag_ratings[tag] = tag_ratings.get(tag, 0) + score
        # sort the tags by rating in descending order
        sorted_tags = sorted(tag_ratings.items(), key=lambda x: x[1], reverse=True)
        for tag in sorted_tags:
            for word in excluded_words:
                if word in tag[0]:
                    sorted_tags.remove(tag)
        return sorted_tags[:limit]
    else:
        print("Unsupported API")
        return []
    
def get_api_related_characters(tag):
    url = f"https://danbooru.donmai.us/related_tag.json?query={tag}&category=4&limit=1000"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()['related_tags']
    # category 4 tags are character tags
    # return only character tags
    return [tag for tag in data if tag['tag']['category'] == 4]
    # return data['related_tags']  # This gives tags related to the specified query

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

# used to get relevant characters based on a tag
def get_relevant_characters(tag,tag_cap=50):
    forbiddenCategories = [1, 5, 3]
    forbiddenTags = ["loli", "shota", "guro", "gore", "scat", "furry", "bestiality","lolidom"]
    apiTags = get_api_related_characters(tag)
    print(f"Found {len(apiTags)} related tags...")

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
        apiTags = get_api_related_characters(tag)

    # tags_by_postcount = sorted(apiTags, key=lambda x: x['tag']['post_count'], reverse=True)
    # return [tag['tag']['name'] for tag in tags_by_postcount if tag['tag']['name'] not in forbiddenTags and tag['tag']['category'] not in forbiddenCategories][:tag_cap]

    apiTags = [tag for tag in apiTags if "censored" not in tag['tag']['name'] and "monochrome" not in tag['tag']['name']]

    # sort the tags by jaccard similarity
    jaccard_tags = sorted(apiTags,key=lambda x: x['jaccard_similarity'], reverse=True)
    jaccard_tags = [tag['tag']['name'] for tag in jaccard_tags if tag['tag']['name'] not in forbiddenTags and tag['tag']['category'] not in forbiddenCategories]

    jaccard_tags = jaccard_tags[1:tag_cap]


    # sort the tags by cosine similarity
    cosine_tags = sorted(apiTags, key=lambda x: x['cosine_similarity'], reverse=True)
    cosine_tags = [tag['tag']['name'] for tag in cosine_tags if tag['tag']['name'] not in forbiddenTags and tag['tag']['category'] not in forbiddenCategories]

    cosine_tags = cosine_tags[1:tag_cap]


    # sort the tags by overlap coefficient
    overlap_tags = sorted(apiTags, key=lambda x: x['overlap_coefficient'], reverse=True)
    overlap_tags = [tag['tag']['name'] for tag in overlap_tags if tag['tag']['name'] not in forbiddenTags and tag['tag']['category'] not in forbiddenCategories]

    overlap_tags = overlap_tags[1:tag_cap]

    # merge the tags while removing duplicates and keeping the order
    final_tags = list(dict.fromkeys(jaccard_tags + cosine_tags))
    return final_tags