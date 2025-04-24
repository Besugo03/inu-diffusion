import json
import os

def saveDefaultsToFile(defaults, filename):
    """
    Save the defaults to a file.
    
    **defaults**: dictionary containing the defaults to save.
    
    **filename**: name of the file to save the defaults to.
    """
    # check if the file exists
    if os.path.exists(filename):
        # load the existing defaults
        with open(filename, "r", encoding="utf-8") as f:
            existingDefaults = json.load(f)
            f.close()
        # update the existing defaults with the new ones
        existingDefaults.update(defaults)
        defaults = existingDefaults
    # save the defaults to the file
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(defaults, f, indent=4)
        f.close()

def loadDefaultsFromFile(filename):
    """
    Load the defaults from a file.
    
    **filename**: name of the file to load the defaults from.
    
    Returns a dictionary containing the defaults.
    """
    # check if the file exists
    if os.path.exists(filename):
        # load the defaults from the file
        with open(filename, "r", encoding="utf-8") as f:
            defaults = json.load(f)
            f.close()
        return defaults
    else:
        return {}