from typing import Literal

forbiddenWords_default = ["censor", "loli", "futa"]
forbiddenWords_colorThemes = ["aqua_theme","black_theme","blue_theme","brown_theme","green_theme","grey_theme","orange_theme","pink_theme","purple_theme","red_theme","white_theme","yellow_theme","anime_coloring","flat_color","gradient","ff_gradient","greyscale","high_contrast","inverted_colors","monochrome","color_drain","multiple_monochrome","spot_color","muted_color","pale_color","partially_colored","pastels","sepia","color_connection","colorized","colorful","spot_color"]
forbiddenWords_bodyFeatues = []
forbiddenWords_attireAndAccessories = []
forbiddenWords_colors = ["black","blue","green","orange","pink","plaid","purple","red","striped","white","yellow","aqua","brown","amber","light","gold","grey","hazel","lavender","maroon","silver",]

def loadForbiddenWords():
    with open("scraped_attire_accessories_etc.txt", "r") as file:
        for line in file:
            forbiddenWords_attireAndAccessories.append(line.strip().lower())
    with open("scraped_body_features.txt", "r", encoding="utf-8") as file:
        for line in file:
            forbiddenWords_bodyFeatues.append(line.strip().lower())

def ensureForbiddenWordsLoaded():
    if len(forbiddenWords_attireAndAccessories) == 0 or len(forbiddenWords_bodyFeatues) == 0:
        loadForbiddenWords()

# filter out forbidden words from the prompt. any of the 4 lists can be passed as the forbiddenWords parameter
# as "default", "colorThemes", "bodyFeatures", "attireAndAccessories" or a combination of multiple of them
def filterForbiddenWords(original_prompt : str, forbiddenWordsLists : Literal["default", "colorThemes", "bodyFeatures", "attireAndAccessories", "colors"]) -> str:
    ensureForbiddenWordsLoaded()
    promptList = original_prompt.split(",")
    filteredPrompt = ""
    for word in promptList:
        if "default" in forbiddenWordsLists and any(defaultword in word.strip().lower().replace(" ", "_") for defaultword in forbiddenWords_default):
            continue
        if "colorThemes" in forbiddenWordsLists and word.strip().lower().replace(" ", "_") in forbiddenWords_colorThemes:
            continue
        if "bodyFeatures" in forbiddenWordsLists and any(bodyFeature in word.strip().lower().replace(" ", "_") for bodyFeature in forbiddenWords_bodyFeatues):
            continue
        if "attireAndAccessories" in forbiddenWordsLists and word.strip().lower().replace(" ", "_") in forbiddenWords_attireAndAccessories:
            continue
        if "colors" in forbiddenWordsLists and any(color in word.strip().lower().replace(" ", "_") for color in forbiddenWords_colors):
            continue
        filteredPrompt += word + ","
    return filteredPrompt[:-1]

# print(filterForbiddenWords("1girl, loli,", ["default","colors"])) # returns "1girl"
testString = "1girl, after vaginal, aftersex, anger vein, annoyed, black hair, black panties, blue eyes, blush, braid, breasts, censored, cum, cum in pussy, cumdrip, double v, fake phone screenshot, fake screenshot, female pubic hair, heart, heart censor, large breasts, low twin braids, nipples, nude, open clothes, open shirt, panties, panties around leg, pubic hair, pussy, shirt, sitting, solo, spread legs, twin braids, underwear, v, white shirt"

print(filterForbiddenWords(testString, ["default","bodyFeatures"]))