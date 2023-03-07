import data_and_settings as settings

# Get all abbreviations from the settings dictionary
def get_all_abbreviations():
    # Initialize empty dictionary to store abbreviations
    abbreviation = {}

    # Iterate over the items in the settings dictionary
    for key, value in settings.SETTINGS.items():
        # If value is a string and 2 characters long, add to abbreviations dictionary
        if isinstance(value, str) and len(value) == 2:
            abbreviation[value] = key

    # Return the abbreviations dictionary
    return abbreviation

# Get the long name for an abbreviation
def get_long_name(abbreviation):
    # Iterate over the items in the settings dictionary
    for key, value in settings.SETTINGS.items():
        # If value matches the abbreviation, return the capitalized key
        if value == abbreviation:
            return key.capitalize()
    # Return None if abbreviation not found
    return None
