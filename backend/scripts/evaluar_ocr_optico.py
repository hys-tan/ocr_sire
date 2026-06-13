import sys
import os
import json
import time
import re
import csv
import logging
from tqdm import tqdm

# Add the backend root directory to sys.path so we can import 'app'
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

from app.services.ocr_service import process_document

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("EvaluadorOptico")

def normalize_text(text: str) -> str:
    """Elimina espacios, caracteres especiales y convierte a minúsculas para comparar puramente letras/números."""
    if not text:
        return ""
    text = str(text).lower()
    # Eliminar cualquier caracter que no sea letra o número
    text = re.sub(r'[^a-z0-9]', '', text)
    return text

def aplanar_valores(data, prefijo=""):
    """Aplana un diccionario anidado para obtener una lista de tuplas (campo, valor)"""
    items = []
    if isinstance(data, dict):
        for k, v in data.items():
            nuevo_prefijo = f"{prefijo}.{k}" if prefijo else k
            items.extend(aplanar_valores(v, nuevo_prefijo))
    elif isinstance(data, list):
        pass # Por ahora no hay listas en el ground truth
    else:
        items.append((prefijo, str(data)))
    return items

def evaluar_optico():
    dataset_file = os.path.join(BASE_DIR, "test", "dataset", "extraccion.json")
    images_dir = os.path.join(BASE_DIR, "test", "images")
    output_md = os.path.join(BASE_DIR, "test", "dataset", "metrics_tesseract_optico.md")
    output_csv = os.path.join(BASE_DIR, "test", "dataset", "metrics_tesseract_optico.csv")
    
    if not os.path.exists(dataset_file):
        logger.error(f"Archivo de dataset no encontrado: {dataset_file}")
        return
        
    with open(dataset_file, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)
        
    totales_por_campo = {}
    aciertos_por_campo = {}
    
    # Metricas por calidad
    totales_por_calidad = {"limpia": 0, "baja": 0}
    aciertos_por_calidad = {"limpia": 0, "baja": 0}
    
    resultados_csv = []
    
    start_total = time.time()
    
    # Lista de archivos a procesar
    archivos = list(ground_truth.keys())
    
    for filename in tqdm(archivos, desc="Procesando Documentos"):
        data_gt = ground_truth[filename]
        calidad = data_gt.get("calidad", "desconocida").lower()
        if calidad not in totales_por_calidad:
            totales_por_calidad[calidad] = 0
            aciertos_por_calidad[calidad] = 0
            
        file_path = os.path.join(images_dir, filename)
        if not os.path.exists(file_path):
            # Buscar variaciones de extensión (ej. .PDF vs .pdf)
            base_name = os.path.splitext(filename)[0]
            posibles = [f for f in os.listdir(images_dir) if os.path.splitext(f)[0] == base_name]
            if posibles:
                file_path = os.path.join(images_dir, posibles[0])
            else:
                logger.warning(f"Archivo de imagen no encontrado: {file_path}")
                continue
                
        # Extraer texto crudo usando el servicio
        try:
            resultado_ocr = process_document(file_path)
            texto_crudo = resultado_ocr.get("text", "")
        except Exception as e:
            logger.error(f"Error procesando {filename}: {e}")
            texto_crudo = ""
            
        texto_crudo_normalizado = normalize_text(texto_crudo)
        
        # Iterar sobre los campos a evaluar (ignorar la key 'calidad')
        campos_a_evaluar = aplanar_valores(data_gt)
        
        for campo, valor_gt in campos_a_evaluar:
            if campo == "calidad":
                continue
                
            valor_gt_norm = normalize_text(valor_gt)
            
            # Si el valor esperado está vacío, ignorar
            if not valor_gt_norm:
                continue
                
            totales_por_campo[campo] = totales_por_campo.get(campo, 0) + 1
            totales_por_calidad[calidad] += 1
            
            # Verificar si el valor esperado es un substring del OCR crudo
            acierto = valor_gt_norm in texto_crudo_normalizado
            
            if acierto:
                aciertos_por_campo[campo] = aciertos_por_campo.get(campo, 0) + 1
                aciertos_por_calidad[calidad] += 1
                
            resultados_csv.append({
                "Archivo": filename,
                "Calidad": calidad,
                "Campo": campo,
                "Valor_Esperado": valor_gt,
                "Acierto": 1 if acierto else 0
            })
            
    end_total = time.time()
    
    # -- Generar Reportes --
    
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Archivo", "Calidad", "Campo", "Valor_Esperado", "Acierto"])
        writer.writeheader()
        writer.writerows(resultados_csv)
        
    # Calcular promedios
    total_campos_evaluados = sum(totales_por_campo.values())
    total_aciertos = sum(aciertos_por_campo.values())
    precision_global = (total_aciertos / total_campos_evaluados * 100) if total_campos_evaluados > 0 else 0
    
    with open(output_md, "w", encoding="utf-8") as f:
        f.write("# Reporte de Evaluación Óptica (OCR) - Tesseract Puro\n\n")
        f.write(f"**Fecha:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Tiempo total de ejecución:** {end_total - start_total:.2f} segundos\n")
        f.write(f"**Total de documentos evaluados:** {len(archivos)}\n\n")
        
        f.write("## 1. Métrica Global (Reconocimiento Óptico)\n\n")
        f.write(f"**Precisión Global Óptica:** {precision_global:.2f}% ({total_aciertos}/{total_campos_evaluados} campos)\n\n")
        
        f.write("## 2. Precisión por Calidad de Documento\n\n")
        for cal in sorted(totales_por_calidad.keys()):
            if totales_por_calidad[cal] > 0:
                acc = (aciertos_por_calidad[cal] / totales_por_calidad[cal]) * 100
                f.write(f"- **{cal.capitalize()}:** {acc:.2f}% ({aciertos_por_calidad[cal]}/{totales_por_calidad[cal]})\n")
        f.write("\n")
        
        f.write("## 3. Precisión Óptica por Campo\n\n")
        f.write("| Campo | Aciertos | Total | Precisión |\n")
        f.write("|---|---|---|---|\n")
        for campo in sorted(totales_por_campo.keys()):
            total_c = totales_por_campo[campo]
            aciertos_c = aciertos_por_campo.get(campo, 0)
            acc_c = (aciertos_c / total_c) * 100 if total_c > 0 else 0
            f.write(f"| {campo} | {aciertos_c} | {total_c} | {acc_c:.2f}% |\n")
            
    logger.info(f"Evaluación finalizada. Precisión Global Óptica: {precision_global:.2f}%")
    logger.info(f"Reporte guardado en {output_md}")
    
if __name__ == "__main__":
    evaluar_optico()
