import os
import requests
import concurrent.futures
import time
import dotenv

forbidden_terms = ["aqua","black","blue","brown","green","grey","orange","purple","pink","red","white","yellow","amber","dark","girl","boy","artist","text","official","futanari","loli"]

# Configuration
# api = rule34 or danbooru
API_CONFIG = {
    'api': 'danbooru',  # Change to 'danbooru' to use the Danbooru API
    'danbooru': {
        'base_url': 'https://danbooru.donmai.us',
        'username': dotenv.get_key('.env','DANBOORU_USERNAME'),
        'api_key': dotenv.get_key('.env','DANBOORU_API_KEY')
    }
}

def fetch_danbooru_posts_by_tag(tag, limit=200):
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

def fetch_all_danbooru_posts(limit=1000, hot_posts=True):
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
            'limit': 200 if limit > 200 else limit,
        }
        if before_id:
            params['page'] = f'b{before_id}'
        
        if hot_posts:
            params['tags'] = 'order:rank'
        
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
    
def get_popular_tags(post_limit, tag_limit=10):
    """Fetches the most popular tags from Danbooru."""
    base_url = API_CONFIG['danbooru']['base_url']
    username = API_CONFIG['danbooru']['username']
    api_key = API_CONFIG['danbooru']['api_key']
    
    params = {
        'login': username,
        'api_key': api_key,
        # 'order': 'count',
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
    
def get_most_scoring_characters(post_limit=1000,results_limit=10, excluded_words=[], hot_posts=False):
    """Fetches the most popular tags from the API (by recent posts) 
    and weights them based on the posts score."""
    if API_CONFIG['api'] == 'rule34':
        RULE34_API_URL = "https://api.rule34.xxx/index.php?page=dapi&s=tag&q=index"
        if hot_posts:
            RULE34_API_URL += "&query=order%3Arank"
        params = {
            'order': 'count',
            'limit': results_limit
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
        return sorted_tags[:results_limit]
    else:
        print("Unsupported API")
        return []
    
def get_related_characters(tag, rank_enabled = False, min_score = 0):
    url = f"https://danbooru.donmai.us/related_tag.json?query={tag}&category=4&limit=1000"
    #? this other one considers the ranks aswell, pretty cool
    if rank_enabled: 
        url = f"https://danbooru.donmai.us/related_tag.json?query=order%3Arank+{tag}&category=4&limit=1000"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()['related_tags']

    # category 4 tags are character tags so we will only return those
    return [tag for tag in data if tag['tag']['category'] == 4]

def nearest_tag(input_tag, characters_only=False):
    url = f"https://danbooru.donmai.us/tags.json?search[name_matches]={input_tag}*&limit=1000"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    
    # Sort tags by post_count in descending order
    sorted_tags = sorted(data, key=lambda tag: tag['post_count'], reverse=True)
    # Extract the names of sorted tags
    if characters_only:
        matching_tags = [tag['name'] for tag in sorted_tags if tag['category'] == 4]
        # print(matching_tags)
    else : 
        matching_tags = [tag['name'] for tag in sorted_tags]
    return matching_tags

def boy_or_girl(tag : str) -> str:
    """Given a tag, it searches all its related tags. 
    If it finds it's strongly related to 'girl' tags (1girl, multiple girls) it returns 'girl'
    If it finds it's strongly related to 'boy' tags (1boy, multiple boys) it returns 'boy'.
    If it does not find any of the above, it returns 'unknown'."""
    # if the tag is not valid, we will try to find the nearest tag to it
    boy_tags = ["1boy","male focus","multiple boys","2boys","3boys","4boys","5boys","6+boys"]
    girl_tags = ["1girl","2girls","3girls","4girls","5girls","6+girls","multiple girls"]
    print(f"Looking for {tag}'s sex... ", end="")
    related_tags_endpoint = f"https://danbooru.donmai.us/related_tag.json?query={tag}"
    response = requests.get(related_tags_endpoint)
    response.raise_for_status()
    data = response.json()['related_tags']
    if data == []:
        tag = nearest_tag(tag, characters_only=True)[0]
        print(f"No entries found. Assuming you ment '{tag}'. Proceeding with this tag...")
        response = requests.get(f"https://danbooru.donmai.us/related_tag.json?query={tag}")
        response.raise_for_status()
        data = response.json()['related_tags']
    for tag in data:
        if tag['tag']['name'] in boy_tags:
            print("boy found.")
            return "boy"
        if tag['tag']['name'] in girl_tags:
            print("girl found.")
            return "girl"
    print("unknown.")
    return "unknown"

def get_relevant_characters(tag,tag_cap=50, rank_enabled=False, min_score=0):
    MINIMUM_POSTS = 1500
    forbiddenCategories = [1, 5, 3]
    apiTags = get_related_characters(tag, rank_enabled, min_score)
    # if apiTags == [] it probably means the tag was not written correctly.
    # in that case, we will try to find the nearest tag to the input tag
    if apiTags == []:
        print(f"Tag {tag} not found...")
        tag = nearest_tag(tag)
        if tag == []:
            print("No similar tags found. Exiting...")
            return []
        else:
            tag = tag[0]
        print(f"Assuming you ment '{tag}'. Proceeding with this tag...")
        apiTags = get_related_characters(tag)

    return [tag['tag']['name'] for tag in apiTags if tag['tag']['post_count'] > MINIMUM_POSTS and tag['tag']['category'] not in forbiddenCategories][:tag_cap]

def search_characters_by_tags(tag, tag_cap=50, post_limit=2000):
    characterCategory = 4

    # check if the tag is actually a correct tag
    
    
    results = fetch_danbooru_posts_by_tag(tag, limit=post_limit)
    tags = [tag for post in results for tag in post['tag_string_character'].split()]
    
    tag_counts = {}
    for tag in tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    # remove all boys
    to_remove = []
    for tag in sorted_tags[:tag_cap+10]:
        if boy_or_girl(tag[0]) == "boy":
            to_remove.append(tag)
    for tag in to_remove:
        sorted_tags.remove(tag)
    print(sorted_tags[:tag_cap])
    # print a string made up of the tags name formatted in the way { tag | tag | tag ...}
    print("{"+(" | ".join([tag[0] for tag in sorted_tags[:tag_cap]]))+"}")

def fetch_uncommon_tags(input_tag, num_tags, return_wildcard=True):
    # query the related tags endpoint with the tag
    related_tags_endpoint = f"https://danbooru.donmai.us/related_tag.json?query={input_tag}&limit=1000"
    response = requests.get(related_tags_endpoint).json()

    # we will now calculate a similarity to score ratio.
    # basically, if a tag is not really close to the input tag, and the two tags are associated with a high scoring in various posts,
    # we will consider the tag as an 'interesting' tag.

    # first, we will get the tags associated with the input tag
    related_tags = [tag['tag']['name'] for tag in response['related_tags'] if tag['tag']['category'] == 0]
    print(len(related_tags))
    # remove all the tags that have a color in them (they are problably hair/eye colors)
    # the colors will be substrings of the tag
    related_tags = [tag for tag in related_tags if not any(color in tag for color in forbidden_terms)]
    far_tags = related_tags[150:250]

    far_tags_data = {}
    for tag in far_tags:
        search = f"{tag}%20{input_tag}"
        print(f"Searching for tag {search}".replace("%20"," "))
        scores = requests.get(f"https://danbooru.donmai.us/posts.json?tags={search}&limit=200").json()
        # print(f"Found {len(scores)} posts for tag {search}".replace("%20"," "))
        scores = [post['score'] for post in scores]
        average_score = sum(scores) / len(scores)
        max_score = max(scores)
        print(f"Average score: {average_score}, Max score: {max_score}")
        far_tags_data[tag] = (average_score,max_score)
    sorted_tags_average = sorted(far_tags_data.items(), key=lambda x: x[1][0], reverse=True)
    sorted_tags_max = sorted(far_tags_data.items(), key=lambda x: x[1][1], reverse=True)
    print(sorted_tags_average)
    # return the average scores (only the names)
    tags = [tag[0] for tag in sorted_tags_average][:num_tags]
    if return_wildcard:
        wildcard = "{"
        for tag in tags:
            wildcard += f"{tag} | "
        wildcard = wildcard[:-3] + "}"
        return wildcard
    else:
        return tags

def parallel_fetch_uncommon_tags(input_tag, num_tags, tag_cap, return_wildcard=True, max_workers=25, delay=0.1):
    # query the related tags endpoint with the tag
    related_tags_endpoint = f"https://danbooru.donmai.us/related_tag.json?query={input_tag}&limit=1000"
    response = requests.get(related_tags_endpoint).json()

    # first, we will get the tags associated with the input tag
    related_tags = [tag['tag']['name'] for tag in response['related_tags'] if tag['tag']['category'] == 0]
    print(len(related_tags))
    # remove all the tags that have a color in them (they are probably hair/eye colors)
    related_tags = [tag for tag in related_tags if not any(color in tag for color in forbidden_terms)]
    far_tags = related_tags[150:250]

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
    sorted_tags_average = sorted(far_tags_data.items(), key=lambda x: x[1][0], reverse=True)
    sorted_tags_max = sorted(far_tags_data.items(), key=lambda x: x[1][1], reverse=True)
    print(sorted_tags_average)
    # return the average scores (only the names)
    tags = [tag[0] for tag in sorted_tags_average][:tag_cap]
    if return_wildcard:
        wildcard = "{"
        wildcard += f"{num_tags}$$"
        for tag in tags:
            wildcard += f"{tag} | "
        wildcard = wildcard[:-3] + "}"
        return wildcard
    else:
        return tags