import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger("ExtractorSIRE.Confidence")

def clean_word_for_lookup(w: str) -> str:
    return w.lower().strip(".,:-_?¿!¡()[]{}'\"/\\")

def get_tesseract_confidence(val_str: str, word_confidences: Dict[str, List[int]]) -> float:
    """
    Calcula la confianza promedio de Tesseract para las palabras que componen el valor.
    Devuelve un float entre 0.0 y 100.0, o -1.0 si no se encuentra ninguna palabra.
    """
    if not val_str or not word_confidences:
        return -1.0
        
    words = val_str.split()
    found_confs = []
    
    for w in words:
        lookup = clean_word_for_lookup(w)
        if lookup in word_confidences:
            # Tomamos la confianza más alta registrada para esa palabra
            found_confs.append(max(word_confidences[lookup]))
            
    if found_confs:
        return sum(found_confs) / len(found_confs)
    return -1.0

def validar_ruc(ruc: str) -> bool:
    """Valida si un RUC tiene formato peruano de 11 dígitos y prefijo válido."""
    if not ruc:
        return False
    return bool(re.match(r'^(10|15|17|20)\d{9}$', ruc))

def validar_fecha(fecha: str) -> bool:
    """Valida formato DD/MM/YYYY y rangos de fecha lógicos."""
    if not fecha:
        return False
    match = re.match(r'^(\d{2})/(\d{2})/(\d{4})$', fecha)
    if not match:
        return False
    d, m, y = map(int, match.groups())
    return 1 <= d <= 31 and 1 <= m <= 12 and 1900 <= y <= 2100

def calcular_confidence_hibrida(
    field_name: str,
    field_dict: Dict[str, Any],
    word_confidences: Dict[str, List[int]],
    all_extracted: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Calcula el score híbrido (0-100) y ajusta el nivel de confianza (ALTA, MEDIA, BAJA)
    para un campo extraído.
    """
    val = field_dict.get("valor")
    estrategia = field_dict.get("estrategia", "Fallback")
    base_score = field_dict.get("score", 20)
    
    if val is None or val == "No detectado" or val == 0 or val == 0.0:
        return {
            "valor": val,
            "confianza": "BAJA",
            "estrategia": estrategia,
            "score": 0
        }
        
    val_str = str(val)
    tess_conf = get_tesseract_confidence(val_str, word_confidences)
    
    # 1. Puntuación por Estrategia de Extracción
    score = base_score
    
    # 2. Incorporación de Confianza de Tesseract
    if tess_conf != -1.0:
        # Combinamos 60% estrategia (heurística) y 40% Tesseract native confidence
        score = int(0.6 * score + 0.4 * tess_conf)
    
    # 3. Validaciones de Negocio y Formato (Penalizaciones/Bonificaciones)
    if field_name in ("emisor_ruc", "receptor_ruc_dni"):
        if validar_ruc(val_str):
            score = max(score, 85)  # Si es un RUC válido de 11 dígitos, mínimo 85%
        else:
            score = min(score, 40)  # Penalizar si es inválido
            
    elif field_name == "fecha_emision":
        if validar_fecha(val_str):
            score = max(score, 80)
        else:
            score = min(score, 45)
            
    elif field_name in ("serie", "numero"):
        # Validar serie F/B/E seguida de 3 letras/dígitos y número de 1 a 8 dígitos
        if field_name == "serie":
            if re.match(r'^[FBE][A-Z0-9]{3}$', val_str, re.IGNORECASE):
                score = max(score, 90)
            else:
                score = min(score, 50)
        elif field_name == "numero":
            if re.match(r'^\d{1,8}$', val_str):
                score = max(score, 90)
            else:
                score = min(score, 50)
                
    # 4. Cuadratura Matemática para Montos
    if field_name in ("subtotal", "igv", "total") and all_extracted:
        montos = all_extracted.get("montos", {})
        subtotal = montos.get("subtotal", {}).get("valor", 0.0)
        igv = montos.get("igv", {}).get("valor", 0.0)
        total = montos.get("total", {}).get("valor", 0.0)
        
        try:
            subtotal_f = float(subtotal) if subtotal else 0.0
            igv_f = float(igv) if igv else 0.0
            total_f = float(total) if total else 0.0
            
            # Si cuadra matemáticamente la ecuación subtotal + igv = total
            if subtotal_f > 0 and igv_f > 0 and total_f > 0:
                if abs(subtotal_f + igv_f - total_f) < 0.05:
                    # ¡Cuadratura matemática perfecta! Subir al 99% de confianza
                    score = 99
                    logger.info(f"Cuadratura matemática detectada para montos. Score de {field_name} sube a 99%")
        except (ValueError, TypeError):
            pass

    # Asegurar rango 0-100
    score = max(0, min(100, score))
    
    # Determinar el nivel cualitativo de confianza basado en el score final
    if score >= 80:
        conf_level = "ALTA"
    elif score >= 55:
        conf_level = "MEDIA"
    else:
        conf_level = "BAJA"
        
    res_dict = dict(field_dict)
    res_dict["confianza"] = conf_level
    res_dict["score"] = score
    return res_dict

def enriquecer_lote_con_confianza_hibrida(
    extracted_data: Dict[str, Any],
    word_confidences: Dict[str, List[int]]
) -> Dict[str, Any]:
    """
    Enriquece todo el JSON extraído calculando y aplicando las confianzas híbridas.
    """
    if not word_confidences:
        return extracted_data
        
    result = {
        "comprobante": {},
        "emisor": {},
        "receptor": {},
        "montos": {}
    }
    
    # Campos directos de comprobante
    for k, v in extracted_data.get("comprobante", {}).items():
        if isinstance(v, dict) and "valor" in v:
            result["comprobante"][k] = calcular_confidence_hibrida(k, v, word_confidences, extracted_data)
        else:
            result["comprobante"][k] = v
            
    # Campos emisor
    for k, v in extracted_data.get("emisor", {}).items():
        if isinstance(v, dict) and "valor" in v:
            result["emisor"][k] = calcular_confidence_hibrida(f"emisor_{k}", v, word_confidences, extracted_data)
        else:
            result["emisor"][k] = v
            
    # Campos receptor
    for k, v in extracted_data.get("receptor", {}).items():
        if isinstance(v, dict) and "valor" in v:
            result["receptor"][k] = calcular_confidence_hibrida(f"receptor_{k}", v, word_confidences, extracted_data)
        else:
            result["receptor"][k] = v
            
    # Campos montos
    for k, v in extracted_data.get("montos", {}).items():
        if isinstance(v, dict) and "valor" in v:
            result["montos"][k] = calcular_confidence_hibrida(k, v, word_confidences, extracted_data)
        else:
            result["montos"][k] = v
            
    return result
