import requests
import json
import typing
import dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import imageRecreator as ir

base_url = "https://gelbooru.com/"

api_key = dotenv.get_key(".env", "gelbooru-api-key")
user_id = dotenv.get_key(".env", "gelbooru-user-id")

def __getPosts(tags: str, limit=100, pid: int = None) -> typing.List[dict]:
    """Get posts from gelbooru.com with rate limit awareness."""
    posts_url = "/index.php?page=dapi&s=post&q=index&json=1"
    params = {
        "tags": tags,
        "limit": limit,
        "api_key": api_key,
        "user_id": user_id
    }
    if pid is not None:
        params["pid"] = pid

    try:
        response = requests.get(base_url + posts_url, params=params)
        response.raise_for_status()
        response_posts = response.json().get('post', [])
        to_remove = []
        for post in response_posts:
            if 'loli' in post['tags'] or 'shota' in post['tags'] or 'child' in post['tags']:
                to_remove.append(post)
        for post in to_remove:
            response_posts.remove(post)
        return response_posts
    except Exception as e:
        print(f"Error fetching posts (pid={pid}): {str(e)}")
        return []

def __getTagInfo(tags: typing.Union[str, list[str]], max_workers: int = 5) -> list:
    """Get tag info with concurrent chunk processing."""
    if isinstance(tags, str):
        tags = tags.split()
    
    tags = list(set(tags))  # Deduplicate first to minimize requests
    results = []
    
    def fetch_chunk(chunk):
        params = {
            "page": "dapi",
            "s": "tag",
            "q": "index",
            "json": 1,
            "names": " ".join(chunk),
            "api_key": api_key,
            "user_id": user_id
        }
        try:
            resp = requests.get(base_url + "/index.php", params=params)
            resp.raise_for_status()
            data = resp.json()
            return data.get('tag', [])
        except Exception as e:
            print(f"Error fetching tags ({len(chunk)} items): {str(e)}")
            return []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Split tags into chunks of 90 (safe margin below 100 limit)
        chunks = [tags[i:i+90] for i in range(0, len(tags), 90)]
        futures = [executor.submit(fetch_chunk, chunk) for chunk in chunks]
        
        for future in as_completed(futures):
            print(f"Processed chunk ({len(results)} tags / {len(tags)} total)")
            results.extend(future.result())

    return results

def getPostTags(pid: typing.Union[int, str]) -> list[str]:
    """Get tags for a specific post."""

    if isinstance(pid, str):
        # https://gelbooru.com/index.php?page=post&s=view&id=11350935&tags=score%3A%3E150
        # match the regex for the id and get the id
        pid = re.search(r'id=(\d+)', pid).group(1)
        print(pid)
        pid = int(pid)

    post_url = f"/index.php?page=dapi&s=post&q=index&json=1&id={pid}"
    response = requests.get(base_url + post_url)
    response.raise_for_status()
    post = response.json().get('post', [])[0]['tags']
    # print(post)
    return post.split()

def filterTagsCategory(tags: list[str], category: typing.Union[int, list[int]]) -> list[str]:
    """Filter tags by category.
    0 = General
    1 = Copyright
    3 = Artist
    4 = Character

    Tags need to be passed as a list of strings.
    """
    if isinstance(category, str):
        category = [category]
    
    tag_info = __getTagInfo(tags)
    return [
        tag['name']
        for tag in tag_info
        if tag.get('type') in category
    ]

def getTrendingCharacters(pages_to_fetch: int = 20, min_score: int = 100, 
                         post_threads: int = 5, tag_threads: int = 5) -> list[tuple[str, int]]:
    """Get trending characters with controlled multithreading."""
    posts = []
    
    # Concurrent post fetching
    with ThreadPoolExecutor(max_workers=post_threads) as executor:
        futures = {executor.submit(__getPosts, f"score:>{min_score}", 100, pid): pid 
                  for pid in range(pages_to_fetch)}
        
        for future in as_completed(futures):
            pid = futures[future]
            try:
                page_posts = future.result()
                posts.extend(page_posts)
                print(f"Processed page {pid} ({len(page_posts)} posts)")
            except Exception as e:
                print(f"Error processing page {pid}: {str(e)}")

    # Extract and count tags
    all_tags = []
    for post in posts:
        all_tags.extend(post.get('tags', '').split())
    
    if not all_tags:
        return []
    
    # Concurrent tag processing
    unique_tags = list(set(all_tags))
    tags_info = __getTagInfo(unique_tags, max_workers=tag_threads)
    
    # Analyze results
    characters = [
        (tag['name'], all_tags.count(tag['name']))
        for tag in tags_info
        if tag.get('type') == 4  # 4 = character tag type
    ]
    
    return sorted(characters, key=lambda x: x[1], reverse=True)

def getPostsAboveScore(score: int, pages_to_fetch: int = 20, post_threads: int = 5, tag_threads: int = 5) -> list[tuple[str, int]]:
    """Get posts above a score with controlled multithreading."""
    posts = []
    for page in range(pages_to_fetch):
        posts.extend(__getPosts(f"score:>{score}", 100, page))
    return posts

if __name__ == "__main__":
    # Example usage with conservative threading
    # trending = getTrendingCharacters(
    #     pages_to_fetch=25,
    #     min_score=300,
    #     post_threads=5,  # Keep below 10 to avoid rate limits
    #     tag_threads=5    # Tags endpoint might be more sensitive
    # )
    # print(trending)

    
    tags = getPostTags("")
    tags = filterTagsCategory(tags, [0])
    print(tags)
    tags = ",".join(tags)
    tags = ir.filterForbiddenWords(tags, ["default", "accessories", "attireAndAccessories", "colors", "bodyFeatures"])