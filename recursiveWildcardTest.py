import re

def split_respecting_braces(text, delimiter):
    """
    Splits a string by a delimiter, but ignores delimiters
    found inside curly braces {}.

    Args:
        text (str): The string to split.
        delimiter (str): The delimiter character.

    Returns:
        list: A list of strings after splitting, with leading/trailing
              whitespace removed from each part.
    """
    parts = []
    current_part = ""
    brace_level = 0
    for char in text:
        if char == '{':
            brace_level += 1
        elif char == '}':
            # Basic error check: ensure we don't go below level 0
            if brace_level > 0:
                brace_level -= 1

        if char == delimiter and brace_level == 0:
            # Found a delimiter at the top level, add the current part
            parts.append(current_part.strip())
            current_part = "" # Reset for the next part
        else:
            # Append the character to the current part
            current_part += char

    # Add the last part after the loop finishes
    parts.append(current_part.strip())
    return parts

def parse_nested_line(line):
    """
    Parses a line with the specified syntax:
    - Top level split by '|' (respecting braces).
    - Each resulting part is then split by ',' (respecting braces).

    Args:
        line (str): The input line string.

    Returns:
        list: A nested list representing the parsed structure.
    """
    # Step 1: Split the line by '|' at the top level
    top_level_parts = split_respecting_braces(line, '|')

    # Step 2: For each top-level part, split by ',' respecting braces
    result = []
    for part in top_level_parts:
        # The rule is effectively the same for the comma split:
        # split by comma, unless it's inside braces.
        inner_parts = split_respecting_braces(part, ',')
        result.append(inner_parts)

    return result

exampleString = "test, uno, !?{due, tre | !{quattro, cinque}, sei}"
# this should be render out as
# test, uno, {!due, !?tre, !{quattro, !cinque}, !?sei}

def findMatchingBracket(string, start_index):
    stack = 1
    for i in range(start_index + 1, len(string)):
        if string[i] == '{':
            stack += 1
        elif string[i] == '}':
            stack -= 1
            if stack == 0:
                return i
    raise ValueError("Unmatched '{' at index {}".format(start_index))

def findallMatchingBrackets(string):
    stack = []
    result = []
    for i, char in enumerate(string):
        if char == '{':
            stack.append(i)
        elif char == '}':
            if stack:
                start = stack.pop()
                result.append((start, i))
            else:
                raise ValueError("Unmatched '}' at index {}".format(i))
    if stack:
        raise ValueError("Unmatched '{' at indices {}".format(stack))
    return result  # Return the list of tuples
    
# 1. Chiama la funzione sulla stringa
def recursivePromptExpand(prompt : str, givenPrefix = None):
    # 2. vede se c'é il pattern di prefix seguito da una graffa aperta
    matches = re.search(r'[!?&-]{', prompt)
    print("matches: ", matches)
    # 3. se c'é, allora prende l'indice del primo match
    if matches:
        matches = re.search(r'[!?&-]{', prompt).start()
        matchStart = matches
        matchEnd = re.search(r'[!?&-]\{', prompt).end()
        matchPrefixes = prompt[matchStart-1:matchEnd-1]
        print(matchPrefixes)
        bracketEnd = findMatchingBracket(prompt, re.search(r'[!?&-]{', prompt).end())
        # 4. chiama la funzione passando quali sono i prefix passati
        endPrompt = recursivePromptExpand(prompt[matchEnd:bracketEnd], matchPrefixes)
        prompt =  prompt[:matchStart] + "{" + endPrompt + "}" + prompt[bracketEnd+1:]
        
    if givenPrefix is None:
        return prompt
    newPrompt = ""
    tagsList = parse_nested_line(prompt)
    for sublist in tagsList:
        for tag in sublist:
            newPrompt += givenPrefix + tag + ", "
        newPrompt += " | "
    newPrompt = newPrompt[:-2]
    return newPrompt

print(recursivePromptExpand(exampleString))