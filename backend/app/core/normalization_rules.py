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
    """
    if not texto:
        return texto

    for patron, reemplazo in _SIGLAS_JURIDICAS:
        texto = re.sub(patron, reemplazo, texto, flags=re.IGNORECASE)

    return texto


def normalizar_razon_social(texto: str) -> str:
    """
    Normalización completa para una Razón Social.
    """
    if not texto or texto == 'No detectado':
        return texto

    resultado = normalizar_siglas_juridicas(texto)
    resultado = re.sub(r'\s{2,}', ' ', resultado).strip()

    if resultado == resultado.upper() and len(resultado) > 1:
        palabras = resultado.split()
        resultado_tc = []
        siglas_finales = {'S.A.C.', 'S.A.', 'E.I.R.L.', 'S.R.L.', 'S.A.A.', 'S.C.R.L.', 'SAC', 'SA'}
        for palabra in palabras:
            if palabra in siglas_finales or re.match(r'^[A-Z]\.([A-Z]\.)+$', palabra):
                resultado_tc.append(palabra)
            else:
                resultado_tc.append(palabra.capitalize())
        resultado = ' '.join(resultado_tc)

    return resultado


def normalizar_ruc(texto: str) -> str:
    """
    Limpia un RUC de caracteres extraños.
    """
    if not texto:
        return texto
    return re.sub(r'\D', '', texto)


def normalizar_fecha(texto: str) -> str:
    """
    Estandariza fechas al formato DD/MM/YYYY.
    """
    if not texto:
        return texto
    match = re.match(r'^(\d{2})\s*[\/\.\-]\s*(\d{2})\s*[\/\.\-]\s*(\d{4})$', texto.strip())
    if match:
        d, m, y = match.groups()
        return f'{d}/{m}/{y}'
    return texto


def normalizar_monto(valor: float) -> float:
    if valor is None:
        return valor
    return round(valor, 2)

def correccion_contextual_numerica(texto: str) -> str:
    """
    Mejora: Si sabemos que el contexto es un número o monto,
    corregimos letras que el OCR suele confundir con números.
    """
    if not texto:
        return texto
    
    # Mapeo de confusiones OCR comunes en contexto estrictamente numérico
    mapa_errores = {
        'O': '0',
        'o': '0',
        'I': '1',
        'l': '1',
        'S': '5',
        's': '5',
        'B': '8',
        'Z': '2',
        'z': '2',
        ',': '.'
    }
    
    resultado = ""
    for char in texto:
        if char in mapa_errores:
            resultado += mapa_errores[char]
        else:
            resultado += char
            
    # Eliminar cualquier cosa que no sea dígito o punto
    resultado = re.sub(r'[^\d\.]', '', resultado)
    return resultado
