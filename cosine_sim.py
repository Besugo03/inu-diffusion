from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os

import metadata

# Function to process and clean the tags
def preprocess_tags(tag_list):
    # Split by commas, remove extra spaces, and convert to lowercase
    return [tag.strip().lower() for tag in tag_list.split(',') if tag.strip()]

# Function to group lists based on similarity
def group_tag_lists(tag_lists, threshold=0.5):
    # Preprocess each tag list
    processed_lists = [' '.join(preprocess_tags(tag_list)) for tag_list in tag_lists]
    
    # Convert the tag lists into a matrix of token counts
    vectorizer = CountVectorizer().fit_transform(processed_lists)
    vectors = vectorizer.toarray()

    # Calculate cosine similarity between the lists
    similarity_matrix = cosine_similarity(vectors)
    
    # Group lists based on a similarity threshold
    groups = []
    used = set()
    
    for i in range(len(tag_lists)):
        if i in used:
            continue
        # Create a new group
        group = [tag_lists[i]]
        used.add(i)
        for j in range(i + 1, len(tag_lists)):
            if similarity_matrix[i][j] >= threshold:
                group.append(tag_lists[j])
                used.add(j)
        groups.append(group)
    
    return groups

# Example usage
if __name__ == "__main__":
    # Example tag lists (each representing tags for different images)
    # tag_lists = [
    #     "cat, animal, cute, furry, whiskers",
    #     "dog, animal, cute, furry, tail",
    #     "landscape, nature, mountain, river",
    #     "cat, whiskers, pet, furry, animal",
    #     "dog, tail, pet, animal, fur",
    #     "nature, mountain, river, forest",
    # ]
    
    tag_lists = []
    image_folder = "/mnt/KingstonSSD/stable-diffusion-webui-forge/output/txt2img-images/2024-10-17"
    for file_name in os.listdir(image_folder):
        if file_name.endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(image_folder, file_name)
            tag_lists.append(metadata.extract_prompt(image_path)[0])

    # Grouping tag lists based on similarity with a threshold of 0.5
    grouped_tags = group_tag_lists(tag_lists, threshold=1)
    
    # Output the groups
    for idx, group in enumerate(grouped_tags):
        print(f"Group {idx + 1}:")
        for tags in group:
            print(f"  {tags}")
