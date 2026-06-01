"""
Servicio de Normalización Inteligente de Datos OCR
====================================================
Orquesta la aplicación de reglas del core sobre el JSON extraído.
"""

from app.core.normalization_rules import (
    normalizar_razon_social,
    normalizar_ruc,
    normalizar_fecha,
    normalizar_monto
)

def aplicar_normalizacion(campo: str, field_dict: dict) -> dict:
    """
    Aplica la normalización correspondiente según el nombre del campo.
    Devuelve el mismo dict enriquecido con 'valor_normalizado'.

    Si el valor normalizado es idéntico al original, NO añade el campo
    (para no generar ruido en el JSON de respuesta).
    """
    if not field_dict or field_dict.get('valor') is None:
        return field_dict

    valor_original = field_dict['valor']
    valor_normalizado = valor_original

    if campo in ('emisor_razon_social', 'receptor_razon_social'):
        valor_normalizado = normalizar_razon_social(str(valor_original))

    elif campo in ('emisor_ruc', 'receptor_ruc_dni'):
        valor_normalizado = normalizar_ruc(str(valor_original))

    elif campo == 'fecha_emision':
        valor_normalizado = normalizar_fecha(str(valor_original))

    elif campo in ('subtotal', 'igv', 'total'):
        # Para montos, los dejamos como vienen, pero en el futuro podríamos 
        # usar la corrección contextual numérica si vienen en formato texto.
        valor_normalizado = normalizar_monto(valor_original)

    # Solo añadir si realmente difiere del original
    result = dict(field_dict)
    if str(valor_normalizado) != str(valor_original):
        result['valor_normalizado'] = valor_normalizado

    return result
