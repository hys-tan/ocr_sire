import re
import logging

logger = logging.getLogger("ExtractorSIRE")

def clean_ocr_text(raw_text: str) -> str:
    """
    Fase 1: Capa de Limpieza del OCR (Control de Basura).
    Recibe el texto crudo y elimina líneas irrelevantes para que el motor de extracción no se confunda.
    """
    cleaned_lines = []
    lines = raw_text.split('\n')
    
    logger.info(f"Fase 1 - Limpieza Iniciada (Líneas originales: {len(lines)})")
    
    for line in lines:
        line = line.strip()
        
        # Regla 1: Eliminar líneas vacías o extremadamente cortas
        if len(line) < 3:
            continue
            
        # Regla 2: Eliminar marcadores inyectados (ej. "--- Página 1 ---")
        if re.search(r'---\s*[pP][áa]gina\s*\d+\s*---', line):
            continue
            
        # Regla 3: Eliminar líneas compuestas solo por símbolos o puntuación (ej. "-------", "| | |")
        if re.match(r'^[\W_]+$', line):
            continue
            
        # Regla 4: Eliminar URLs obvias
        if "HTTP://" in line.upper() or "HTTPS://" in line.upper() or "WWW." in line.upper():
            continue
            
        # Normalizar espacios múltiples dentro de la línea sobreviviente
        line = re.sub(r'\s+', ' ', line)
        cleaned_lines.append(line)
        
    final_text = '\n'.join(cleaned_lines)
    logger.info(f"Fase 1 - Limpieza Finalizada (Líneas resultantes: {len(cleaned_lines)})")
    return final_text
