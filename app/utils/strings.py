import re


def clean_file_name(name):
    # Reemplazar cualquier carácter que no sea letra,
    # número, guion o guion bajo por un espacio
    clean_name = re.sub(r'[^\w\.-]', ' ', name)
    clean_name = ' '.join(clean_name.split())
    return clean_name

def remove_trailing_spaces(input_string):
    # Strip trailing spaces using rstrip()
    return input_string.rstrip()
