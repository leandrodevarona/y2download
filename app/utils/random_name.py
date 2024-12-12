import random  
import string  

def get_random_name(length=10):  
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))  