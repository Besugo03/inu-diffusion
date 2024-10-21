import requests
from collections import Counter
import statistics
import numpy as np

# Initialize Danbooru API URL
DANBOORU_URL = 'https://danbooru.donmai.us'

def get_exponential_decay_threshold(tag_counts):
    """
    Calculate a dynamic threshold using an exponential decay function based on tag frequencies.
    
    Parameters:
    tag_counts (Counter): The counts of tags.
    
    Returns:
    float: The exponential decay threshold.
    """
    frequencies = np.array(list(tag_counts.values()))
    mean = np.mean(frequencies)
    std_dev = np.std(frequencies)
    
    # Exponential decay threshold based on mean and standard deviation
    decay_threshold = mean * np.exp(-std_dev / mean)
    
    return decay_threshold

def get_co_occurrence_score(tag, tag_counts, total_posts):
    """
    Calculate a co-occurrence score for each tag based on its frequency and the total number of posts.
    
    Parameters:
    tag (str): The main tag.
    tag_counts (Counter): The counts of tags.
    total_posts (int): The total number of posts analyzed.
    
    Returns:
    dict: Co-occurrence score for each tag.
    """
    co_occurrence_scores = {t: (count / total_posts) * (count / (tag_counts[tag] + 1)) for t, count in tag_counts.items() if t != tag}
    return co_occurrence_scores

def get_related_tags(tag, ban_tags=None, initial_limit=100, max_pages=10, min_posts=500):
    """
    Given a tag, get related tags from Danbooru using robust pagination and filtering.
    
    Parameters:
    tag (str): The main tag to find related tags for.
    ban_tags (list of str): Tags to exclude from the results.
    initial_limit (int): Number of posts to analyze per page.
    max_pages (int): Maximum number of pages to fetch.
    min_posts (int): Minimum total number of posts to fetch.
    
    Returns:
    dict: Dictionary of filtered tags with their occurrences, sorted by occurrences.
    list of str: List of related tags excluding less relevant ones and banned tags.
    """
    if ban_tags is None:
        ban_tags = []

    all_tags = []
    total_posts = 0
    page = 1

    # Fetch posts with robust pagination
    while total_posts < min_posts and page <= max_pages:
        response = requests.get(f'{DANBOORU_URL}/posts.json?tags={tag}&limit={initial_limit}&page={page}')
        response.raise_for_status()  # Raise an error for bad responses
        posts = response.json()

        if not posts:
            break  # Stop if no more posts are returned

        total_posts += len(posts)

        for post in posts:
            all_tags.extend(post.get('tag_string_general', '').split())

        page += 1

    # Count the occurrence of each tag
    tag_counts = Counter(all_tags)

    # Print and sort the dictionary of all tags with their occurrences
    sorted_tag_dict = dict(sorted(tag_counts.items(), key=lambda item: item[1], reverse=True))
    print("Tag occurrences dictionary (sorted):")
    print(sorted_tag_dict)

    # Calculate dynamic thresholds
    mean_frequency = statistics.mean(tag_counts.values())
    median_frequency = statistics.median(tag_counts.values())
    decay_threshold = get_exponential_decay_threshold(tag_counts)

    # Determine the final threshold using the average of mean, median, and exponential decay
    dynamic_threshold = (mean_frequency + median_frequency + decay_threshold) / 3

    # Filter tags by the dynamic threshold and exclude the main tag and banned tags
    filtered_tags = {t: count for t, count in tag_counts.items() if t != tag and t not in ban_tags and count >= dynamic_threshold}

    # Calculate co-occurrence score
    co_occurrence_scores = get_co_occurrence_score(tag, tag_counts, total_posts)

    # Further filter by co-occurrence score: tags should have a significant co-occurrence score
    relevance_threshold = 0.02  # Adjust the threshold based on required relevance
    final_tags = [t for t in filtered_tags if co_occurrence_scores.get(t, 0) >= relevance_threshold]

    return sorted_tag_dict, final_tags

# Example usage
main_tag = "femdom"
ban_tags = []

sorted_tag_dict, related_tags = get_related_tags(main_tag, ban_tags, min_posts=1200)
print(f"\nRelated tags for '{main_tag}': {related_tags}")
