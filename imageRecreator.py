from typing import Literal

forbiddenWords_default = ["censor", "loli", "futa", "artist", "logo", "patreon","virtual_youtuber", "text", "bubble", "signature", "watermark"]
forbiddenWords_colorThemes = ["aqua_theme","black_theme","blue_theme","brown_theme","green_theme","grey_theme","orange_theme","pink_theme","purple_theme","red_theme","white_theme","yellow_theme","anime_coloring","flat_color","gradient","ff_gradient","greyscale","high_contrast","inverted_colors","monochrome","color_drain","multiple_monochrome","spot_color","muted_color","pale_color","partially_colored","pastels","sepia","color_connection","colorized","colorful","spot_color"]
forbiddenWords_bodyFeatues = []
forbiddenWords_attireAndAccessories = []
forbiddenWords_colors = ["black","blue","green","orange","pink","plaid","purple","red","striped","white","yellow","aqua","brown","amber","light","gold","grey","hazel","lavender","maroon","silver",]
forbidden_accessories = []


def loadForbiddenWords():
    with open("scraped_attire_accessories_etc.txt", "r") as file:
        for line in file:
            forbiddenWords_attireAndAccessories.append(line.strip().lower())
    with open("scraped_body_features.txt", "r", encoding="utf-8") as file:
        for line in file:
            forbiddenWords_bodyFeatues.append(line.strip().lower())
    with open("accessories_only.txt", "r", encoding="utf-8") as file:
        for line in file:
            forbidden_accessories.append(line.strip().lower())

# TODO to implement interrogation do deepbooru to add more tags to the image
def enrichImageTags():
    print("Enriching image tags...")

def ensureForbiddenWordsLoaded():
    if len(forbiddenWords_attireAndAccessories) == 0 or len(forbiddenWords_bodyFeatues) == 0:
        loadForbiddenWords()

# filter out forbidden words from the prompt. any of the 4 lists can be passed as the forbiddenWords parameter
# as "default", "colorThemes", "bodyFeatures", "attireAndAccessories" or a combination of multiple of them
def filterForbiddenWords(original_prompt : str, forbiddenWordsLists : Literal["default", "colorThemes", "bodyFeatures", "accessories", "attireAndAccessories", "colors"]) -> str:
    ensureForbiddenWordsLoaded()
    promptList = original_prompt.split(",")
    filteredPrompt = ""
    for word in promptList:
        if "default" in forbiddenWordsLists and any(defaultword in word.strip().lower().replace(" ", "_") for defaultword in forbiddenWords_default):
            print(f"filtered out {word} (default), matched with")
            continue
        if "colorThemes" in forbiddenWordsLists and word.strip().lower().replace(" ", "_") in forbiddenWords_colorThemes:
            print(f"filtered out {word} (colorThemes)")
            continue
        if "bodyFeatures" in forbiddenWordsLists and any(bodyFeature in word.strip().lower().replace(" ", "_") for bodyFeature in forbiddenWords_bodyFeatues):
            print(f"filtered out {word} (bodyFeatures)")
            continue
        if "accessories" in forbiddenWordsLists and any(accessory in word.strip().lower().replace(" ", "_") for accessory in forbidden_accessories):
            matchedword = [accessory for accessory in forbidden_accessories if accessory in word.strip().lower().replace(" ", "_")]
            print(f"filtered out {word} (accessories) matched with {matchedword}")
            continue
        if "attireAndAccessories" in forbiddenWordsLists and any(attire in word.strip().lower().replace(" ", "_") for attire in forbiddenWords_attireAndAccessories):
            print(f"filtered out {word} (attireAndAccessories)")
            continue
        if "colors" in forbiddenWordsLists and any(color in word.strip().lower().replace(" ", "_") for color in forbiddenWords_colors):
            print(f"filtered out {word} (colors)")
            continue
        filteredPrompt += word + ","
    return filteredPrompt[:-1]



# tests
if __name__ == "__main__":
    # print(filterForbiddenWords("1girl, loli,", ["default","colors"])) # returns "1girl"
    testString = ""
    # print(filterForbiddenWords(testString, ["default","bodyFeatures"]))