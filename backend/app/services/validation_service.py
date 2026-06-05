from typing import Dict, Any
from app.core.validators import is_valid_ruc, validate_math_logic
from app.core.comprobante_utils import build_and_set_serie_numero
from app.core.normalization_rules import normalizar_numero_sunat

def validate_math(montos: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fase 3: Validación Matemática (Orquestación).
    Usa el validador del core para asegurar la coherencia de Subtotal, IGV y Total.
    Si hubo error matemático del OCR, ajusta los scores y etiquetas del diccionario.
    """
    subtotal = montos["subtotal"]["valor"]
    igv = montos["igv"]["valor"]
    total = montos["total"]["valor"]
    
    nuevo_sub, nuevo_igv, fue_corregido = validate_math_logic(subtotal, igv, total)
    
    if fue_corregido:
        montos["subtotal"]["confianza"] = "BAJA"
        montos["igv"]["confianza"] = "BAJA"
        montos["subtotal"]["estrategia"] = "Corregido matemáticamente (OCR falló)"
        montos["igv"]["estrategia"] = "Corregido matemáticamente (OCR falló)"
        montos["subtotal"]["score"] = 30
        montos["igv"]["score"] = 30
        
    if total > 0:
        # Actualizamos siempre para corregir errores
        montos["subtotal"]["valor"] = nuevo_sub
        montos["igv"]["valor"] = nuevo_igv
        montos["total"]["confianza"] = "ALTA"
        montos["total"]["score"] = 90  # Total validado matemáticamente
        
    return montos

def clean_extracted_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fase 5: Post-procesamiento (Orquestación).
    Limpia, capitaliza y coordina validaciones antes de enviarlo al cliente.
    """
    # 1. Limpiar Razones Sociales (Title Case para verse profesional)
    emisor_rs = data["emisor"]["razon_social"]["valor"]
    if emisor_rs and emisor_rs != "No detectado":
        data["emisor"]["razon_social"]["valor"] = emisor_rs.title()
        
    receptor_rs = data["receptor"]["razon_social"]["valor"]
    if receptor_rs and receptor_rs != "No detectado":
        data["receptor"]["razon_social"]["valor"] = receptor_rs.title()
        
    # 2. Validar RUC matemáticamente y ajustar confianza
    emisor_ruc = data["emisor"]["ruc"]["valor"]
    if emisor_ruc and not is_valid_ruc(emisor_ruc):
        data["emisor"]["ruc"]["valor"] = f"{emisor_ruc} (Inválido)"
        data["emisor"]["ruc"]["confianza"] = "BAJA"
        data["emisor"]["ruc"]["estrategia"] = "Error Validación: Módulo 11 falló"
        data["emisor"]["ruc"]["score"] = 10
        
    receptor_ruc = data["receptor"]["ruc_dni"]["valor"]
    if receptor_ruc and len(receptor_ruc) == 11 and not is_valid_ruc(receptor_ruc):
        data["receptor"]["ruc_dni"]["valor"] = f"{receptor_ruc} (Inválido)"
        data["receptor"]["ruc_dni"]["confianza"] = "BAJA"
        data["receptor"]["ruc_dni"]["estrategia"] = "Error Validación: Módulo 11 falló"
        data["receptor"]["ruc_dni"]["score"] = 10
        
    # 3. Número SUNAT — campo separado (Opción C)
    # Se genera numero_sunat desde el número crudo extraído por el OCR.
    # NO se sobreescribe el número original. Solo se añade el campo estandarizado.
    numero_field = data["comprobante"].get("numero")
    if numero_field and numero_field.get("valor"):
        resultado_sunat = normalizar_numero_sunat(str(numero_field["valor"]))
        data["comprobante"]["numero_sunat"] = resultado_sunat["numero_sunat"]
        data["comprobante"]["numero_sunat_advertencia"] = resultado_sunat["advertencia"]
    else:
        data["comprobante"]["numero_sunat"] = None
        data["comprobante"]["numero_sunat_advertencia"] = "Número no detectado"

    # 4. Validar Serie y Número
    # Utilizamos el core comprobante_utils para construir y validar la serie/numero.
    build_and_set_serie_numero(
        data["comprobante"],
        sep='-',
        validate=True,
        adjust_confidence=True,
        penalty=20
    )
        
    # 4. Cuadratura Matemática de Montos
    data["montos"] = validate_math(data["montos"])
    
    return data

