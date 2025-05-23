import re


def clean_file_name(name):
    # Replace not allowed characters for a space
    clean_name = re.sub(r'[^\w\.-]', ' ', name)
    clean_name = ' '.join(clean_name.split())
    return clean_name

def remove_trailing_spaces(input_string):
    # Strip trailing spaces using rstrip()
    return input_string.rstrip()

def remove_leading_spaces(input_string):
    # Strip trailing spaces using lstrip()
    return input_string.lstrip()

def filter_numeric_format_id(items):
    #Filters a list of dictionaries, keeping only those with a numeric 'format_id'
    return [item for item in items if isinstance(item.get("format_id"), str) and item["format_id"].isdigit()]

def filter_format_id(list):
    # Ensures the first occurrence is retained in case 'format_id' is duplicate
    seen = set()
    filtered_list = []

    for item in list:
        if item['format_id'] not in seen:
            filtered_list.append(item)
            seen.add(item['format_id'])

    return filtered_list
 