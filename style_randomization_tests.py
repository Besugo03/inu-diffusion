import random

# Example style_tags list and variations value
style_tags = ["asura \(asurauser\)", "gsusart", "sarukaiwolf", "lentiyay", "buzzlyears", "enn_matien", "ratatatat74", "mizumizuni", "ebora", "shexyo", "riz" ]

variations = 50
n_tags = 3

# generate three random strengths for each style tag
# between 0 and 1, rounded to 0.05

wildcard = "{"

for var in range(variations):
    # make a temporary subset of n_tags style tags
    random.shuffle(style_tags)
    style_tags_subset = style_tags[:n_tags] 
    strengths = [round(random.uniform(0, 1), 2) for _ in range(len(style_tags_subset))]
    
    # generate the style tag string for that variation
    style_tag_string = ""
    for idx, style_tag in enumerate(style_tags_subset):
        style_tag_string += f"{style_tag}:{strengths[idx]},"
    style_tag_string = style_tag_string[:-1]
wildcard = wildcard[:-3] + "}"

print(wildcard)