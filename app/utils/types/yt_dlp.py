from enum import Enum

class Quality(Enum):
    HIGHT = 1080
    MEDIUM = 720
    LOW= 360

    def validate_quality(value):  
        for quality in Quality:  
            if isinstance(quality.value, int):  # Para comprobar si se trata de un número  
                if value == quality.value:  
                    return True
        return False
    
    def get_quality(value):  
        if isinstance(value, int):  # Si es un número  
            for quality in Quality:  
                if quality.value == value:  
                    return quality  
        elif isinstance(value, str):  # Si es un string  
            try:  
                return Quality[value.upper()]  # Convierte el string a mayúsculas para hacer la búsqueda  
            except KeyError:  
                return Quality.HIGHT
        else:
            return Quality.HIGHT
