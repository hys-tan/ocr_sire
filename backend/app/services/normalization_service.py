"""
Servicio de Normalización Inteligente de Datos OCR
====================================================
Normaliza textos extraídos por OCR sin destruir el valor original.
Específicamente orientado a las reglas ortográficas del SUNAT (Perú).

Principio: NO alterar agresivamente. Solo corregir patrones conocidos
           que el OCR fragmenta de forma predecible y recurrente.
"""

import re

# ─── Tipos de Persona Jurídica ─────────────────────────────────────────────────
# El OCR suele fragmentar las siglas porque las lee como palabras separadas.
# Se define como (patrón_regex_flexible, reemplazo_correcto).

_SIGLAS_JURIDICAS = [
    # Sociedades más comunes en Perú
    (r'\bS\s*\.?\s*A\s*\.?\s*C\s*\.?\b',       'S.A.C.'),   # Sociedad Anónima Cerrada
    (r'\bS\s*\.?\s*A\s*\.?\b',                  'S.A.'),     # Sociedad Anónima
    (r'\bE\s*\.?\s*I\s*\.?\s*R\s*\.?\s*L\s*\.?\b', 'E.I.R.L.'),  # Empresa Individual de Resp. Limitada
    (r'\bS\s*\.?\s*R\s*\.?\s*L\s*\.?\b',       'S.R.L.'),   # Sociedad de Responsabilidad Limitada
    (r'\bS\s*\.?\s*A\s*\.?\s*A\s*\.?\b',       'S.A.A.'),   # Sociedad Anónima Abierta
    (r'\bS\s*\.?\s*C\s*\.?\s*R\s*\.?\s*L\s*\.?\b', 'S.C.R.L.'),  # Soc. Comercial de Resp. Limitada
    # Variantes sin separación de espacios (lectura OCR compacta)
    (r'\bSAC\b',    'S.A.C.'),
    (r'\bEIRL\b',   'E.I.R.L.'),
    (r'\bSRL\b',    'S.R.L.'),
    (r'\bSAA\b',    'S.A.A.'),
    (r'\bSCRL\b',   'S.C.R.L.'),
]

# ─── Abreviaciones de dirección comunes (limpieza posterior) ───────────────────
_ABREV_DIRECCION = [
    (r'\bAv\s*\.?\s+', 'Av. '),
    (r'\bJr\s*\.?\s+', 'Jr. '),
    (r'\bCa\s*\.?\s+', 'Ca. '),    # Calle abreviada
    (r'\bUrb\s*\.?\s+', 'Urb. '),
]


def normalizar_siglas_juridicas(texto: str) -> str:
    """
    Corrige siglas de tipo jurídico que el OCR fragmenta con espacios.

    Ejemplos:
      "S A C"       → "S.A.C."
      "E I R L"     → "E.I.R.L."
      "SAC"         → "S.A.C."
      "S.A.C"       → "S.A.C."   (punto final faltante)

    El reemplazo es case-insensitive pero preserva el formato correcto
    en mayúsculas (que es la convención del SUNAT).
    """
    if not texto:
        return texto

    for patron, reemplazo in _SIGLAS_JURIDICAS:
        texto = re.sub(patron, reemplazo, texto, flags=re.IGNORECASE)

    return texto


def normalizar_razon_social(texto: str) -> str:
    """
    Normalización completa para una Razón Social:
    1. Corrige siglas jurídicas fragmentadas.
    2. Elimina espacios dobles residuales.
    3. Convierte a Title Case solo si está en mayúsculas puras
       (el OCR suele devolver TODO EN MAYÚSCULAS).

    El texto original nunca se sobreescribe — esta función solo
    retorna el valor normalizado para mostrarlo al usuario.
    """
    if not texto or texto == 'No detectado':
        return texto

    resultado = normalizar_siglas_juridicas(texto)

    # Eliminar espacios dobles que puedan quedar tras el reemplazo
    resultado = re.sub(r'\s{2,}', ' ', resultado).strip()

    # Title Case solo si viene completamente en mayúsculas
    # (evitar transformar textos que ya tienen capitalización correcta)
    if resultado == resultado.upper() and len(resultado) > 1:
        # Preservar siglas jurídicas que ya están correctas
        palabras = resultado.split()
        resultado_tc = []
        siglas_finales = {'S.A.C.', 'S.A.', 'E.I.R.L.', 'S.R.L.', 'S.A.A.', 'S.C.R.L.', 'SAC', 'SA'}
        for palabra in palabras:
            if palabra in siglas_finales or re.match(r'^[A-Z]\.([A-Z]\.)+$', palabra):
                resultado_tc.append(palabra)  # sigla → dejar en mayúsculas
            else:
                resultado_tc.append(palabra.capitalize())
        resultado = ' '.join(resultado_tc)

    return resultado


def normalizar_ruc(texto: str) -> str:
    """
    Limpia un RUC de caracteres extraños que el OCR puede introducir.
    Solo conserva dígitos.
    """
    if not texto:
        return texto
    return re.sub(r'\D', '', texto)


def normalizar_fecha(texto: str) -> str:
    """
    Estandariza fechas al formato DD/MM/YYYY.
    Acepta separadores: . - / o espacios.
    """
    if not texto:
        return texto
    match = re.match(r'^(\d{2})\s*[\/\.\-]\s*(\d{2})\s*[\/\.\-]\s*(\d{4})$', texto.strip())
    if match:
        d, m, y = match.groups()
        return f'{d}/{m}/{y}'
    return texto


def normalizar_monto(valor: float) -> float:
    """
    Redondea a 2 decimales para evitar artefactos de punto flotante.
    """
    if valor is None:
        return valor
    return round(valor, 2)


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
        valor_normalizado = normalizar_monto(valor_original)

    # Solo añadir si realmente difiere del original
    result = dict(field_dict)
    if str(valor_normalizado) != str(valor_original):
        result['valor_normalizado'] = valor_normalizado

    return result
