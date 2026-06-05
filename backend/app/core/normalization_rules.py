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


def normalizar_numero_sunat(numero_raw: str) -> dict:
    """
    Estandariza el número de comprobante al formato de 8 dígitos exigido por SUNAT.

    Regla SUNAT: El correlativo siempre debe ser de 8 dígitos con ceros a la izquierda.
    Ej: 123 → 00000123 | 12345 → 00012345

    Para evitar confusión con ceros ya presentes en el número crudo:
    - Si el número crudo ya tiene 8 dígitos: se devuelve tal cual (sin tocar).
    - Si tiene menos de 8: se aplica zfill(8) y se registra en 'numero_sunat'.
    - Si tiene más de 8: valor anómalo, se devuelve advertencia y sin normalización.

    Devuelve un dict con:
      - numero_sunat: str | None  (valor estandarizado, o None si no aplica)
      - advertencia: str | None   (mensaje si hay algo sospechoso)
    """
    if not numero_raw:
        return {"numero_sunat": None, "advertencia": "Número no detectado"}

    # Solo los dígitos importan para el formato SUNAT
    solo_digitos = re.sub(r'\D', '', str(numero_raw).strip())

    if not solo_digitos:
        return {"numero_sunat": None, "advertencia": "El OCR no extrajo dígitos del número"}

    longitud = len(solo_digitos)

    if longitud == 8:
        # Ya tiene el formato correcto — no se modifica
        return {"numero_sunat": solo_digitos, "advertencia": None}
    elif longitud < 8:
        # Padding estándar SUNAT
        padded = solo_digitos.zfill(8)
        return {"numero_sunat": padded, "advertencia": None}
    else:
        # Más de 8 dígitos: anómalo (posible OCR doble lectura)
        return {
            "numero_sunat": None,
            "advertencia": f"Número con {longitud} dígitos (esperado ≤ 8). Verificar manualmente."
        }


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
