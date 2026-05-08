import re
import unicodedata
import logging
from typing import Dict, Any

# Configurar Logging para auditar estrategias y facilitar debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()] # En producción añadir FileHandler
)
logger = logging.getLogger("ExtractorSIRE")

# Tabla de puntuaciones por estrategia (basada en las reglas del Plan V8)
SCORE_POR_ESTRATEGIA: Dict[str, int] = {
    # Regex exactas → 95-100
    "Regex (11 dígitos, prefijo válido)": 96,
    "Regex Serie-Número": 97,
    "Keyword/Prefijo Serie": 95,
    "Keyword": 95,
    "Regex (Flex-Separators)": 94,
    "Regex Keyword (USD)": 95,
    # Heurísticas / keywords secundarias → 70-85
    "Est. 2 - Keyword Inline 'DENOMINACIÓN'": 85,
    "Est. 2 - Keyword Inline": 82,
    "Est. 3 - Keyword Siguiente Línea": 78,
    "Est. 1 - Proximidad RUC": 72,
    "Est. 4 - Bloque Superior Mayúsculas": 70,
    # Inferencia / cálculo derivado → 50-70
    "Default Nacional": 65,
    "Valor Max (Heurística)": 62,
    "Cálculo desde Total (18%)": 58,
    # Fallos → 0-30
    "Default": 25,
    "Fallback": 20,
    "No detectado": 0,
}

def calcular_score(estrategia: str, confianza: str) -> int:
    """Devuelve el score numérico (0-100) según la estrategia y nivel de confianza."""
    # Intentar match exacto primero
    if estrategia in SCORE_POR_ESTRATEGIA:
        return SCORE_POR_ESTRATEGIA[estrategia]
    # Fallback por nivel de confianza
    if confianza == "ALTA":
        return 88
    if confianza == "MEDIA":
        return 60
    return 20

def extract_ruc(text: str) -> list:
    """Extrae todos los RUCs válidos."""
    estrategia = "Regex (11 dígitos, prefijo válido)"
    rucs = re.findall(r'\b(?:10|15|17|20)\d{9}\b', text)
    return [{
        "valor": r,
        "confianza": "ALTA",
        "estrategia": estrategia,
        "score": calcular_score(estrategia, "ALTA")
    } for r in rucs]

def extract_serie_numero(text: str) -> Dict[str, Any]:
    """Extrae la serie y número combinados (mantenido para compatibilidad con extract_tipo_comprobante)."""
    match = re.search(r'\b([FBE]\w{3})\s*-\s*(\d{1,8})\b', text, re.IGNORECASE)
    if match:
        estrategia = "Regex Serie-Número"
        return {"valor": f"{match.group(1).upper()}-{match.group(2)}", "confianza": "ALTA", "estrategia": estrategia, "score": calcular_score(estrategia, "ALTA")}
    return {"valor": None, "confianza": "BAJA", "estrategia": "No detectado", "score": 0}

def extract_serie(text: str) -> Dict[str, Any]:
    """Extrae SOLO la serie del comprobante (ej: F001, B002)."""
    match = re.search(r'\b([FBE]\w{3})\s*-\s*\d{1,8}\b', text, re.IGNORECASE)
    if match:
        estrategia = "Regex Serie-Número"
        return {"valor": match.group(1).upper(), "confianza": "ALTA", "estrategia": estrategia, "score": calcular_score(estrategia, "ALTA")}
    return {"valor": None, "confianza": "BAJA", "estrategia": "No detectado", "score": 0}

def extract_numero(text: str) -> Dict[str, Any]:
    """Extrae SOLO el número correlativo del comprobante (ej: 0083104)."""
    match = re.search(r'\b[FBE]\w{3}\s*-\s*(\d{1,8})\b', text, re.IGNORECASE)
    if match:
        estrategia = "Regex Serie-Número"
        return {"valor": match.group(1), "confianza": "ALTA", "estrategia": estrategia, "score": calcular_score(estrategia, "ALTA")}
    return {"valor": None, "confianza": "BAJA", "estrategia": "No detectado", "score": 0}

def extract_tipo_comprobante(text: str, serie_dict: dict) -> Dict[str, Any]:
    """Determina el tipo de comprobante."""
    texto_upper = text.upper()
    serie = serie_dict["valor"] if serie_dict else None
    
    if "FACTURA" in texto_upper or (serie and serie.startswith('F')):
        estrategia = "Keyword/Prefijo Serie"
        return {"valor": "Factura Electrónica", "confianza": "ALTA", "estrategia": estrategia, "score": calcular_score(estrategia, "ALTA")}
    elif "BOLETA" in texto_upper or (serie and serie.startswith('B')):
        estrategia = "Keyword/Prefijo Serie"
        return {"valor": "Boleta de Venta Electrónica", "confianza": "ALTA", "estrategia": estrategia, "score": calcular_score(estrategia, "ALTA")}
    elif "NOTA DE CRÉDITO" in texto_upper or "NOTA DE CREDITO" in texto_upper:
        estrategia = "Keyword"
        return {"valor": "Nota de Crédito", "confianza": "ALTA", "estrategia": estrategia, "score": calcular_score(estrategia, "ALTA")}
    return {"valor": "Desconocido", "confianza": "BAJA", "estrategia": "Fallback", "score": calcular_score("Fallback", "BAJA")}

def extract_fecha(text: str) -> Dict[str, Any]:
    """Extrae y normaliza la fecha."""
    match = re.search(r'\b(\d{2})\s*[/.\-:]\s*(\d{2})\s*[/.\-:]\s*(\d{4})\b', text)
    if match:
        dia, mes, anio = match.groups()
        estrategia = "Regex (Flex-Separators)"
        return {"valor": f"{dia}/{mes}/{anio}", "confianza": "ALTA", "estrategia": estrategia, "score": calcular_score(estrategia, "ALTA")}
    return {"valor": None, "confianza": "BAJA", "estrategia": "No detectado", "score": 0}

def extract_montos(text: str) -> Dict[str, Any]:
    """Busca montos (Subtotal, IGV, Total) devolviendo dicts de confianza."""
    montos = {
        "subtotal": {"valor": 0.0, "confianza": "BAJA", "estrategia": "Default", "score": calcular_score("Default", "BAJA")},
        "igv":      {"valor": 0.0, "confianza": "BAJA", "estrategia": "Default", "score": calcular_score("Default", "BAJA")},
        "total":    {"valor": 0.0, "confianza": "BAJA", "estrategia": "Default", "score": calcular_score("Default", "BAJA")}
    }
    
    cantidades = re.findall(r'\b\d{1,3}(?:,\d{3})*\.\d{2}\b', text)
    if not cantidades:
        return montos
        
    valores = []
    for c in cantidades:
        try:
            val = float(c.replace(',', ''))
            valores.append(val)
        except ValueError:
            pass
            
    if valores:
        posible_total = max(valores)
        est_total = "Valor Max (Heurística)"
        montos["total"] = {"valor": posible_total, "confianza": "MEDIA", "estrategia": est_total, "score": calcular_score(est_total, "MEDIA")}
        
        subtotal = round(posible_total / 1.18, 2)
        igv = round(posible_total - subtotal, 2)
        est_calc = "Cálculo desde Total (18%)"
        montos["subtotal"] = {"valor": subtotal, "confianza": "MEDIA", "estrategia": est_calc, "score": calcular_score(est_calc, "MEDIA")}
        montos["igv"]      = {"valor": igv,      "confianza": "MEDIA", "estrategia": est_calc, "score": calcular_score(est_calc, "MEDIA")}
        
    return montos

def extract_moneda(text: str) -> Dict[str, Any]:
    """Detecta PEN o USD."""
    if re.search(r'\b(USD|DOLARES|\$)\b', text, re.IGNORECASE):
        estrategia = "Regex Keyword (USD)"
        return {"valor": "USD", "confianza": "ALTA", "estrategia": estrategia, "score": calcular_score(estrategia, "ALTA")}
    estrategia = "Default Nacional"
    return {"valor": "PEN", "confianza": "MEDIA", "estrategia": estrategia, "score": calcular_score(estrategia, "MEDIA")}

def is_valid_razon_social(text: str) -> bool:
    """Aplica filtros negativos para descartar falsos positivos de Razón Social."""
    text = text.strip()
    if len(text) < 4:
        return False # Demasiado corto
        
    # Descartar si es solo números o símbolos
    if re.match(r'^[\d\W]+$', text):
        return False
        
    # Descartar palabras clave de dirección o detalles (Validación de SUNAT)
    bad_keywords = ["AV.", "AVENIDA", "CALLE", "JIRON", "JR.", "URB.", "MANZANA", "MZ.", "LOTE", "TELEFONO", "TELF", "EMAIL", "CORREO", "LIMA"]
    text_upper = text.upper()
    for kw in bad_keywords:
        if kw in text_upper.split() or text_upper.startswith(kw):
            return False
            
    return True

def limpiar_razon_social(text: str) -> str:
    """
    Limpia el texto de una Razón Social eliminando:
    - Números de RUC o DNI (10, 15, 17, 20 + 9 dígitos)
    - Etiquetas residuales: 'R.U.C.', 'RUC:', 'DNI:', etc.
    - Fragmentos de columnas OCR: 'MONEDA', 'FECHA', 'SOLES', etc.
    - Espacios dobles y caracteres extraños al final
    """
    # 1. Eliminar etiquetas tipo "R.U.C." antes del número
    text = re.sub(r'\bR\.?\s*U\.?\s*C\.?\s*[:\-]?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\bDNI\s*[:\-]?\s*', '', text, flags=re.IGNORECASE)
    
    # 2. Eliminar números de RUC/DNI (secuencias de 8 o 11 dígitos)
    text = re.sub(r'\b\d{11}\b', '', text)
    text = re.sub(r'\b\d{8}\b', '', text)
    
    # 3. Eliminar "ruido de columna" OCR
    cutoffs = ["MONEDA", "FECHA", "TOTAL", "SOLES", "DOLARES", "IMPORTE", "MONTO"]
    for cutoff in cutoffs:
        if cutoff in text.upper():
            text = re.split(cutoff, text, flags=re.IGNORECASE)[0]
    
    # 4. Limpiar puntuación suelta al final y espacios dobles
    text = re.sub(r'[\s\-\.,:;]+$', '', text.strip())
    text = re.sub(r'\s{2,}', ' ', text)
    
    return text.strip()

def normalizar_para_busqueda(texto: str) -> str:
    """
    Normaliza texto SOLO para hacer matching de keywords.
    - Convierte a mayúsculas
    - Elimina tildes vocales (AÉÍÓÚ → AEIOU) pero conserva la Ñ
    - Limpia símbolos raros, conserva letras, números, espacios y Ñ
    - Reduce múltiples espacios a uno
    """
    texto = texto.upper()
    
    # Descomponer caracteres Unicode (NFD) para separar letra + tilde
    nfd = unicodedata.normalize('NFD', texto)
    # Filtrar: conservar todo EXCEPTO las marcas de acento (Mn), pero reponer Ñ
    resultado = []
    for char in nfd:
        # Ignorar marcas diacíriticas (tildes), pero solo si no es parte de Ñ
        if unicodedata.category(char) == 'Mn':
            continue
        resultado.append(char)
    texto = ''.join(resultado)
    
    # Limpiar símbolos dejando solo letras (incluyendo Ñ), números y espacios
    texto = re.sub(r'[^A-Z0-9Ñ\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto)
    
    return texto.strip()

# Patrones flexibles para detectar keywords del receptor.
# Usan \s* para absorber espacios OCR y variantes sin tilde.
PATRONES_RECEPTOR = [
    r'SE[NÑ]OR\s*(?:ES|A)?',          # SEÑORES, SENORES, SEÑOR, SENOR
    r'RAZ[OÒ]N\s+SOCIAL',             # RAZÓN SOCIAL, RAZON SOCIAL
    r'DENOMINACI[OÓ]N',              # DENOMINACIÓN, DENOMINACION
    r'DENOMINACIN',                   # OCR corruption frecuente
    r'ADQUIRENTE',
    r'DESTINATARIO',
    r'CLIENTE\s+FINAL',
]

def extract_razon_social_emisor(lines: list, ruc_line_idx: int) -> Dict[str, str]:
    """Busca la razón social del emisor usando múltiples estrategias."""
    if ruc_line_idx > 0:
        posible_razon = limpiar_razon_social(lines[ruc_line_idx - 1].strip())
        if is_valid_razon_social(posible_razon):
            logger.info(f"Emisor extraído [Est. 1 - Proximidad RUC]: {posible_razon}")
            estrategia = "Est. 1 - Proximidad RUC"
            return {"valor": posible_razon, "confianza": "ALTA", "estrategia": estrategia, "score": calcular_score(estrategia, "ALTA")}
            
    # Estrategia 3: Heurística de Mayúsculas al inicio del documento
    for line in lines[:6]:
        line = limpiar_razon_social(line.strip())
        if line.isupper() and is_valid_razon_social(line):
            logger.info(f"Emisor extraído [Est. 3 - Mayúsculas]: {line}")
            estrategia = "Est. 4 - Bloque Superior Mayúsculas"
            return {"valor": line, "confianza": "MEDIA", "estrategia": estrategia, "score": calcular_score(estrategia, "MEDIA")}
            
    logger.warning("Fallback activado: No se pudo detectar Emisor seguro.")
    return {"valor": "No detectado", "confianza": "BAJA", "estrategia": "Fallback", "score": calcular_score("Fallback", "BAJA")}

def extract_razon_social_receptor(lines: list, receptor_ruc: str = None) -> Dict[str, str]:
    """Busca la razón social del receptor mediante patrones regex flexibles o proximidad al RUC."""

    # Estrategia 2: Búsqueda por patrones keyword (con regex flexible y normalización)
    for i, line in enumerate(lines):
        line_norm = normalizar_para_busqueda(line)  # Solo para matching

        # Ignorar títulos de sección genéricos
        if re.search(r'DATOS\s+DEL\s+CLIENTE', line_norm) and ':' not in line_norm:
            continue

        for patron in PATRONES_RECEPTOR:
            if not re.search(patron, line_norm):
                continue

            # Intento 1: inline con dos puntos  —  KEY : VALOR
            match = re.search(rf'(?:{patron})[^\wÑ:]*:[^\wÑ]*([A-Z0-9Ñ\s.&-]+)', line_norm)
            if not match:
                # Intento 2: inline sin dos puntos  —  KEY VALOR
                match = re.search(rf'(?:{patron})[^\wÑ]*([A-Z0-9Ñ\s.&-]+)', line_norm)

            if match:
                posible_razon = limpiar_razon_social(match.group(1).strip())

                # Cortar si el OCR unió columnas
                for cutoff in [' MONEDA', ' FECHA', ' RUC', ' DNI']:
                    if cutoff in posible_razon:
                        posible_razon = posible_razon.split(cutoff)[0].strip()

                if is_valid_razon_social(posible_razon):
                    logger.info(f"Receptor extraído [Est. 2 - Keyword Inline '{patron}']: {posible_razon}")
                    estrategia = "Est. 2 - Keyword Inline"
                    return {"valor": posible_razon, "confianza": "ALTA", "estrategia": estrategia, "score": calcular_score(estrategia, "ALTA")}

            # Intento 3: el valor está en la siguiente línea
            if i + 1 < len(lines):
                posible_razon = limpiar_razon_social(lines[i + 1].strip())
                if is_valid_razon_social(posible_razon):
                    logger.info(f"Receptor extraído [Est. 3 - Keyword siguiente línea '{patron}']: {posible_razon}")
                    estrategia = "Est. 3 - Keyword Siguiente Línea"
                    return {"valor": posible_razon, "confianza": "MEDIA", "estrategia": estrategia, "score": calcular_score(estrategia, "MEDIA")}

    # Estrategia 4: Proximidad al RUC del Receptor
    if receptor_ruc:
        for i, line in enumerate(lines):
            if receptor_ruc in line:
                candidatos_idx = [i-1, i-2, i+1, i+2]
                for idx in candidatos_idx:
                    if 0 <= idx < len(lines):
                        posible_razon = limpiar_razon_social(lines[idx].strip())
                        if is_valid_razon_social(posible_razon) and not any(k in posible_razon.upper() for k in ["RUC", "FECHA", "MONEDA", "SOLES", "DOLARES", "TOTAL"]):
                            logger.info(f"Receptor extraído [Est. 4 - Proximidad RUC Receptor]: {posible_razon}")
                            estrategia = "Est. 1 - Proximidad RUC"
                            return {"valor": posible_razon, "confianza": "MEDIA", "estrategia": estrategia, "score": calcular_score(estrategia, "MEDIA")}

    logger.warning("Fallback activado: No se pudo detectar Receptor seguro.")
    return {"valor": "No detectado", "confianza": "BAJA", "estrategia": "Fallback", "score": calcular_score("Fallback", "BAJA")}

def parse_invoice(raw_text: str) -> Dict[str, Any]:
    """
    Función orquestadora que toma el texto crudo del OCR y devuelve un JSON
    estructurado con los requerimientos mínimos de SUNAT.
    """
    logger.info("=== Iniciando Pipeline de Extracción ===")
    logger.debug(f"Texto Crudo a procesar:\n{raw_text}")
    
    # El texto ya viene limpio desde cleaning_service.py
    cleaned_text = raw_text.replace('\n', ' ')
    # Lista de líneas para heurísticas estructurales
    lines = raw_text.split('\n')
    
    # RUCs
    rucs = extract_ruc(cleaned_text)
    emisor_ruc_dict = rucs[0] if len(rucs) > 0 else {"valor": None, "confianza": "BAJA", "estrategia": "No detectado", "score": 0}
    receptor_ruc_dict = rucs[1] if len(rucs) > 1 else {"valor": None, "confianza": "BAJA", "estrategia": "No detectado", "score": 0}
    
    # Razones Sociales (Fallback System)
    emisor_ruc_idx = -1
    emisor_ruc_val = emisor_ruc_dict["valor"]
    if emisor_ruc_val:
        for i, line in enumerate(lines):
            if emisor_ruc_val in line:
                emisor_ruc_idx = i
                break
                
    emisor_razon = extract_razon_social_emisor(lines, emisor_ruc_idx)
    receptor_razon = extract_razon_social_receptor(lines, receptor_ruc_dict["valor"])
    
    # Serie, Número y Tipo
    serie_numero = extract_serie_numero(cleaned_text)  # Para inferir tipo
    tipo_comprobante = extract_tipo_comprobante(cleaned_text, serie_numero)
    serie = extract_serie(cleaned_text)
    numero = extract_numero(cleaned_text)
    
    # Fechas y Moneda
    fecha = extract_fecha(cleaned_text)
    moneda = extract_moneda(cleaned_text)
    
    # Montos validados
    montos = extract_montos(cleaned_text)
    
    logger.info("=== Pipeline de Extracción Finalizado ===")
    
    # Estructura de Salida (Todo envuelto en diccionarios de Confianza)
    return {
        "comprobante": {
            "tipo": tipo_comprobante,
            "serie": serie,
            "numero": numero,
            "fecha_emision": fecha,
            "moneda": moneda
        },
        "emisor": {
            "ruc": emisor_ruc_dict,
            "razon_social": emisor_razon
        },
        "receptor": {
            "ruc_dni": receptor_ruc_dict,
            "razon_social": receptor_razon
        },
        "montos": montos
    }

# --- PRUEBA LOCAL ---
if __name__ == "__main__":
    # Texto de prueba extraído de tu captura anterior
    texto_prueba = """
    FILMARG S.A.C.
    ES > VARIEDAD DE FILTROS PARA MAQUINARIA PESADA
    LIMA - LIMA - LOS OLIVOS
    Señor(es): IDELSI SOLUCIONES S.A.C.
    R.U.C. 20601607167
    Factura Electrónica
    F001-0083104
    RUC FECHA TIPO DE MONEDA
    20611758088 - 25/06/2025 Soles
    Total Gravado 1,316.95
    Total IGV (18%) 237.05
    Total 1,554.00
    """
    
    print("=== EXTRACCIÓN DE DATOS (REGLAS SUNAT) ===")
    resultado = parse_invoice(texto_prueba)
    
    import json
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
