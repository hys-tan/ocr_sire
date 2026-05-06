import re
from typing import Dict, Any

def is_valid_ruc(ruc: str) -> bool:
    """
    Fase 3: Validación Estricta.
    Verifica si un string es un RUC peruano válido usando el Algoritmo Módulo 11 (SUNAT).
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

def validate_math(montos: Dict[str, float]) -> Dict[str, float]:
    """
    Fase 3: Validación Matemática.
    Asegura la coherencia de Subtotal, IGV y Total.
    """
    subtotal = montos.get("subtotal", 0.0)
    igv = montos.get("igv", 0.0)
    total = montos.get("total", 0.0)
    
    # Si tenemos el total, forzamos la cuadratura según SUNAT (IGV 18%)
    if total > 0:
        subtotal_calculado = round(total / 1.18, 2)
        igv_calculado = round(total - subtotal_calculado, 2)
        
        # Actualizamos siempre para corregir errores de OCR en el IGV o Subtotal
        montos["subtotal"] = subtotal_calculado
        montos["igv"] = igv_calculado
        
    return montos

def clean_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fase 5: Post-procesamiento.
    Limpia, capitaliza y formatea el JSON final antes de enviarlo al cliente.
    """
    # Limpiar Razones Sociales (Title Case para verse profesional)
    # Ahora razon_social es un dict: {"valor": "...", "confianza": "...", "estrategia": "..."}
    emisor_rs = data["emisor"]["razon_social"]["valor"]
    if emisor_rs and emisor_rs != "No detectado":
        data["emisor"]["razon_social"]["valor"] = emisor_rs.title()
        
    receptor_rs = data["receptor"]["razon_social"]["valor"]
    if receptor_rs and receptor_rs != "No detectado":
        data["receptor"]["razon_social"]["valor"] = receptor_rs.title()
        
    # Validar RUC matemáticamente
    emisor_ruc = data["emisor"]["ruc"]
    if emisor_ruc and not is_valid_ruc(emisor_ruc):
        data["emisor"]["ruc"] = f"{emisor_ruc} (Inválido)"
        
    receptor_ruc = data["receptor"]["ruc_dni"]
    if receptor_ruc and len(receptor_ruc) == 11 and not is_valid_ruc(receptor_ruc):
        data["receptor"]["ruc_dni"] = f"{receptor_ruc} (Inválido)"
        
    # Formatear Montos a 2 decimales string (opcional para el Frontend)
    # Por ahora los dejamos como float, pero aplicamos la cuadratura matemática
    data["montos"] = validate_math(data["montos"])
    
    return data
