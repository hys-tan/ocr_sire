import re

def is_valid_ruc(ruc: str) -> bool:
    """
    Verifica si un string es un RUC peruano válido usando el Algoritmo Módulo 11 (SUNAT).
    Reglas de negocio puras (Core).
    """
    if not ruc or not isinstance(ruc, str):
        return False
        
    ruc = ruc.strip()
    
    # Regla 1: Debe tener 11 dígitos y empezar con 10, 15, 17 o 20
    if not re.match(r'^(10|15|17|20)\d{9}$', ruc):
        return False
        
    # Regla 2: Algoritmo Módulo 11
    factores = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    suma = 0
    for i in range(10):
        suma += int(ruc[i]) * factores[i]
        
    resto = suma % 11
    digito_esperado = 11 - resto
    if digito_esperado == 10:
        digito_esperado = 0
    elif digito_esperado == 11:
        digito_esperado = 1
        
    return int(ruc[10]) == digito_esperado


def validate_math_logic(subtotal: float, igv: float, total: float) -> tuple[float, float, bool]:
    """
    Asegura la coherencia matemática entre Subtotal, IGV y Total.
    Prioriza el total para calcular el subtotal e IGV (18%).
    
    Devuelve: (nuevo_subtotal, nuevo_igv, fue_corregido)
    """
    if total <= 0:
        return subtotal, igv, False
        
    subtotal_calculado = round(total / 1.18, 2)
    igv_calculado = round(total - subtotal_calculado, 2)
    
    fue_corregido = False
    if abs(subtotal - subtotal_calculado) > 1.0 or abs(igv - igv_calculado) > 1.0:
        fue_corregido = True
        
    return subtotal_calculado, igv_calculado, fue_corregido
