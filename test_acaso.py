import random

# Example style_tags list and variations value
style_tags = ["ratatatat74", "ebora", "nyantcha","mizumizuni", "riz","shexyo" ]

variations = 10

# generate three random strengths for each style tag
# between 0 and 1, rounded to 0.05

wildcard = "{"

for var in range(variations):
    strengths = [round(random.uniform(0, 1), 2) for _ in range(len(style_tags))]
    
    # generate the style tag string for that variation
    style_tag_string = ""
    for idx, style_tag in enumerate(style_tags):
        style_tag_string += f"{style_tag}:{strengths[idx]},"
    style_tag_string = style_tag_string[:-1]
    wildcard += f"{style_tag_string} | "
wildcard = wildcard[:-3] + "}"