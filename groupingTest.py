import os
import tkinter as tk
from tkinter import filedialog, Label, Frame, BOTH
from PIL import Image, ImageTk
import metadata  # Assuming this is your custom metadata library

# Step 1: Load Images and Extract Prompts using metadata.extract_prompt()
def load_images_and_prompts(image_folder):
    image_files = []
    prompts = []
    
    for file_name in os.listdir(image_folder):
        if file_name.endswith(('.png', '.jpg', '.jpeg')):
            image_path = os.path.join(image_folder, file_name)
            image_files.append(image_path)

            # Use the metadata library to extract the prompt
            prompt = metadata.extract_prompt(image_path)
            prompts.append(prompt)
            
    return image_files, prompts

# Step 2: Tokenize Prompts into Tags (split by commas)
def tokenize_prompts(prompts):
    tokenized_prompts = []
    for prompt in prompts:
        tags = [tag.strip() for tag in prompt.split(",")]  # Split by comma, remove extra spaces
        tokenized_prompts.append(tags)  # Store tags as list
    return tokenized_prompts

# Step 3: Group images based on common tags (with debug prints)
def group_images_by_tag_similarity(tokenized_prompts, min_common_tags=2):
    n = len(tokenized_prompts)
    labels = [-1] * n  # Label for each image (group index)
    group_id = 0

    print("\n=== DEBUG: Tokenized Prompts ===")
    for i, prompt_tags in enumerate(tokenized_prompts):
        print(f"Image {i}: Tags -> {prompt_tags}")

    for i in range(n):
        if labels[i] == -1:  # If not yet assigned to a group
            labels[i] = group_id  # Create a new group
            print(f"\nAssigning Image {i} to Group {group_id}")
            for j in range(i + 1, n):
                # Count the number of common tags
                common_tags = len(set(tokenized_prompts[i]).intersection(set(tokenized_prompts[j])))
                print(f"Comparing Image {i} and Image {j} -> {common_tags} common tags")
                if common_tags >= min_common_tags:
                    print(f"Grouping Image {j} with Image {i} in Group {group_id}")
                    labels[j] = group_id  # Assign the same group
            group_id += 1

    print("\n=== DEBUG: Final Group Labels ===")
    for i, label in enumerate(labels):
        print(f"Image {i}: Group {label}")

    return labels

# Step 4: Create a GUI to Preview Groups of Images
class ImageClusterGUI:
    def __init__(self, master, image_files, labels):
        self.master = master
        self.master.title("Image Grouping Preview")
        self.image_files = image_files
        self.labels = labels
        self.groups = self.group_images_by_label()
        self.current_group = 0
        self.display_group()

    # Group images by their labels
    def group_images_by_label(self):
        groups = {}
        for idx, label in enumerate(self.labels):
            if label not in groups:
                groups[label] = []
            groups[label].append(self.image_files[idx])

        print("\n=== DEBUG: Grouped Images ===")
        for group_id, images in groups.items():
            print(f"Group {group_id}: {len(images)} images")

        return groups

    # Display all images in the current group
    def display_group(self):
        group_images = self.groups[self.current_group]
        
        # Clear existing widgets from the master window
        for widget in self.master.winfo_children():
            widget.destroy()

        frame = Frame(self.master)
        frame.pack(fill=BOTH, expand=True)

        label = Label(self.master, text=f"Group {self.current_group + 1} ({len(group_images)} images)")
        label.pack()

        # Display images in a grid
        max_columns = 3  # Define how many columns for the grid layout
        for idx, image_file in enumerate(group_images):
            img = Image.open(image_file)
            img = img.resize((150, 150))  # Resize images for display
            img = ImageTk.PhotoImage(img)

            panel = Label(frame, image=img)
            panel.image = img  # Keep a reference to avoid garbage collection
            panel.grid(row=idx // max_columns, column=idx % max_columns, padx=10, pady=10)

        # Button to move to the next group
        button = tk.Button(self.master, text="Next Group", command=self.next_group)
        button.pack()

    # Move to the next group of images
    def next_group(self):
        self.current_group = (self.current_group + 1) % len(self.groups)
        self.display_group()

# Step 5: Main Function to Execute Grouping and GUI
def main():
    # Select image folder
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    image_folder = filedialog.askdirectory(title="Select Image Folder")

    # Load images and extract prompts using the metadata library
    image_files, prompts = load_images_and_prompts(image_folder)

    # Tokenize prompts into tags
    tokenized_prompts = tokenize_prompts(prompts)

    # Group images based on common tags (configurable min_common_tags)
    labels = group_images_by_tag_similarity(tokenized_prompts, min_common_tags=2)  # Adjust threshold as needed

    # Preview GUI
    root.deiconify()  # Show the root window
    gui = ImageClusterGUI(root, image_files, labels)
    root.mainloop()

if __name__ == "__main__":
    main()
