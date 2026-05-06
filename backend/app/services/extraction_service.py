import re
import logging
from typing import Dict, Any

# Configurar Logging para auditar estrategias y facilitar debugging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()] # En producción añadir FileHandler
)
logger = logging.getLogger("ExtractorSIRE")

def extract_ruc(text: str) -> list:
    """Extrae todos los RUCs (11 dígitos que empiezan con 10, 15 o 20) válidos en Perú."""
    return re.findall(r'\b(?:10|15|20)\d{9}\b', text)

def extract_serie_numero(text: str) -> str:
    """Extrae la serie y número (ej. F001-0083104 o B001-123456)."""
    match = re.search(r'\b([FBE]\w{3})\s*-\s*(\d{1,8})\b', text, re.IGNORECASE)
    if match:
        return f"{match.group(1).upper()}-{match.group(2)}"
    return None

def extract_tipo_comprobante(text: str, serie: str) -> str:
    """Determina el tipo de comprobante por texto o por la inicial de la serie."""
    texto_upper = text.upper()
    if "FACTURA" in texto_upper or (serie and serie.startswith('F')):
        return "Factura Electrónica"
    elif "BOLETA" in texto_upper or (serie and serie.startswith('B')):
        return "Boleta de Venta Electrónica"
    elif "NOTA DE CRÉDITO" in texto_upper or "NOTA DE CREDITO" in texto_upper:
        return "Nota de Crédito"
    return "Desconocido"

def extract_fecha(text: str) -> str:
    """Extrae la fecha soportando múltiples separadores OCR (/, -, :, .) y la normaliza a DD/MM/YYYY."""
    # Buscar formato numérico (ej. 16:04:2024, 16/04/2024, 16-04-2024, 16 . 04 . 2024)
    match = re.search(r'\b(\d{2})\s*[/.\-:]\s*(\d{2})\s*[/.\-:]\s*(\d{4})\b', text)
    if match:
        dia, mes, anio = match.groups()
        return f"{dia}/{mes}/{anio}"
    return None

def extract_montos(text: str) -> Dict[str, float]:
    """
    Busca montos (Subtotal, IGV, Total) y usa la lógica de SUNAT (IGV = 18%)
    para intentar deducir o corregir los valores si el OCR falló en alguno.
    """
    montos = {"subtotal": 0.0, "igv": 0.0, "total": 0.0}
    
    # Buscar todos los números con formato decimal (ej: 1,316.95 o 1554.00)
    # Excluimos números larguísimos para no confundir con RUCs o cuentas
    cantidades = re.findall(r'\b\d{1,3}(?:,\d{3})*\.\d{2}\b', text)
    
    if not cantidades:
        return montos
        
    # Convertir a float
    valores = []
    for c in cantidades:
        try:
            val = float(c.replace(',', ''))
            valores.append(val)
        except ValueError:
            pass
            
    # Heurística simple: El Total suele ser el número más grande al final de la factura
    if valores:
        posible_total = max(valores)
        montos["total"] = posible_total
        
        # Lógica SIRE Perú: Si tenemos el Total, podemos calcular el Subtotal y el IGV (18%)
        # Total = Subtotal * 1.18  =>  Subtotal = Total / 1.18
        # IGV = Total - Subtotal
        montos["subtotal"] = round(posible_total / 1.18, 2)
        montos["igv"] = round(posible_total - montos["subtotal"], 2)
        
    return montos

def extract_moneda(text: str) -> str:
    """Detecta PEN (Soles) o USD (Dólares)."""
    if re.search(r'\b(USD|DOLARES|\$)\b', text, re.IGNORECASE):
        return "USD"
    return "PEN" # Por defecto en Perú

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

def extract_razon_social_emisor(lines: list, ruc_line_idx: int) -> Dict[str, str]:
    """Busca la razón social del emisor usando múltiples estrategias."""
    if ruc_line_idx > 0:
        # Estrategia 1: Proximidad al RUC (La línea de arriba)
        posible_razon = lines[ruc_line_idx - 1].strip()
        if is_valid_razon_social(posible_razon):
            logger.info(f"Emisor extraído [Est. 1 - Proximidad RUC]: {posible_razon}")
            return {"valor": posible_razon, "confianza": "ALTA", "estrategia": "Proximidad RUC"}
            
    # Estrategia 3: Heurística de Mayúsculas al inicio del documento
    for line in lines[:6]:
        line = line.strip()
        if line.isupper() and is_valid_razon_social(line):
            logger.info(f"Emisor extraído [Est. 3 - Mayúsculas]: {line}")
            return {"valor": line, "confianza": "MEDIA", "estrategia": "Heurística Mayúsculas Encabezado"}
            
    logger.warning("Fallback activado: No se pudo detectar Emisor seguro.")
    return {"valor": "No detectado", "confianza": "BAJA", "estrategia": "Fallback"}

def extract_razon_social_receptor(lines: list, receptor_ruc: str = None) -> Dict[str, str]:
    """Busca la razón social del receptor mediante keywords o proximidad al RUC."""
    # Eliminamos 'CLIENTE' genérico porque suele chocar con 'DATOS DEL CLIENTE'
    keywords = ["SEÑOR(ES)", "SEÑORES", "RAZÓN SOCIAL", "RAZON SOCIAL", "ADQUIRENTE", "DESTINATARIO", "CLIENTE FINAL", "DENOMINACION", "DENOMINACIÓN", "DENOMINACIN"]
    
    # Estrategia 2: Búsqueda por Keywords (diccionario extendido)
    for i, line in enumerate(lines):
        line_upper = line.upper()
        # Ignorar si es solo un título de sección
        if "DATOS DEL CLIENTE" in line_upper and ":" not in line_upper:
            continue
            
        for kw in keywords:
            if kw in line_upper:
                # Extraer texto después de los dos puntos o caracteres especiales
                match = re.search(rf'{kw}[^\w:]*:[^\w]*([A-Z0-9\s.&-]+)', line_upper)
                if not match:
                    # Intento más relajado si no hay dos puntos
                    match = re.search(rf'{kw}[^\w]*([A-Z0-9\s.&-]+)', line_upper)
                    
                if match:
                    posible_razon = match.group(1).strip()
                    
                    # Limpieza agresiva: si el OCR juntó dos columnas
                    for cutoff in [" MONEDA", " FECHA", " RUC", " DNI"]:
                        if cutoff in posible_razon:
                            posible_razon = posible_razon.split(cutoff)[0].strip()
                            
                    if is_valid_razon_social(posible_razon):
                        logger.info(f"Receptor extraído [Est. 2 - Keyword Inline '{kw}']: {posible_razon}")
                        return {"valor": posible_razon, "confianza": "ALTA", "estrategia": f"Keyword Inline ({kw})"}
                        
                # Si no está en la misma línea, intentar la siguiente línea
                elif i + 1 < len(lines):
                    posible_razon = lines[i + 1].strip()
                    if is_valid_razon_social(posible_razon):
                        logger.info(f"Receptor extraído [Est. 2 - Keyword Próxima Línea '{kw}']: {posible_razon}")
                        return {"valor": posible_razon, "confianza": "MEDIA", "estrategia": f"Keyword Próxima Línea ({kw})"}
                        
    # Estrategia 4: Proximidad al RUC del Receptor
    if receptor_ruc:
        for i, line in enumerate(lines):
            if receptor_ruc in line:
                # Revisar 2 líneas hacia arriba y 2 líneas hacia abajo
                candidatos_idx = [i-1, i-2, i+1, i+2]
                for idx in candidatos_idx:
                    if 0 <= idx < len(lines):
                        posible_razon = lines[idx].strip()
                        # Si es válida y no tiene palabras clave de otros campos
                        if is_valid_razon_social(posible_razon) and not any(k in posible_razon.upper() for k in ["RUC", "FECHA", "MONEDA", "SOLES", "DOLARES", "TOTAL"]):
                            logger.info(f"Receptor extraído [Est. 4 - Proximidad RUC Receptor]: {posible_razon}")
                            return {"valor": posible_razon, "confianza": "MEDIA", "estrategia": "Proximidad RUC Receptor"}
                            
    logger.warning("Fallback activado: No se pudo detectar Receptor seguro.")
    return {"valor": "No detectado", "confianza": "BAJA", "estrategia": "Fallback"}

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
    emisor_ruc = rucs[0] if len(rucs) > 0 else None
    receptor_ruc = rucs[1] if len(rucs) > 1 else None
    
    # Razones Sociales (Fallback System)
    emisor_ruc_idx = -1
    if emisor_ruc:
        for i, line in enumerate(lines):
            if emisor_ruc in line:
                emisor_ruc_idx = i
                break
                
    emisor_razon = extract_razon_social_emisor(lines, emisor_ruc_idx)
    receptor_razon = extract_razon_social_receptor(lines, receptor_ruc)
    
    # Serie, Número y Tipo
    serie_numero = extract_serie_numero(cleaned_text)
    tipo_comprobante = extract_tipo_comprobante(cleaned_text, serie_numero)
    
    # Fechas y Moneda
    fecha = extract_fecha(cleaned_text)
    moneda = extract_moneda(cleaned_text)
    
    # Montos validados
    montos = extract_montos(cleaned_text)
    
    logger.info("=== Pipeline de Extracción Finalizado ===")
    
    # Estructura de Salida
    return {
        "comprobante": {
            "tipo": tipo_comprobante,
            "serie_numero": serie_numero,
            "fecha_emision": fecha,
            "moneda": moneda
        },
        "emisor": {
            "ruc": emisor_ruc,
            "razon_social": emisor_razon
        },
        "receptor": {
            "ruc_dni": receptor_ruc,
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
