import os
import json
import csv
import logging
import difflib
import sys

# Añadir el path base para poder importar servicios de la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Desactivar logs ruidosos
logging.getLogger("ppocr").setLevel(logging.CRITICAL)

from app.services.ocr_service import process_document

def obtener_lineas_ocr(file_path):
    """Ejecuta PaddleOCR en una imagen y devuelve las líneas de texto."""
    result = process_document(file_path)
    return result["text"].split("\n")

def aplanar_ground_truth(gt_dict):
    """Extrae todos los valores no nulos del Ground Truth y los asocia a una clase."""
    valores = []
    
    # Comprobante
    for key in ['tipo', 'serie', 'numero']:
        val = gt_dict.get('comprobante', {}).get(key)
        if val: valores.append((val, "BLOQUE_COMPROBANTE"))
    
    val = gt_dict.get('comprobante', {}).get('fecha_emision')
    if val: valores.append((val, "BLOQUE_FECHA"))
    
    val = gt_dict.get('comprobante', {}).get('moneda')
    if val: valores.append((val, "BLOQUE_MONEDA"))
    
    # Emisor
    for key in ['ruc', 'razon_social']:
        val = gt_dict.get('emisor', {}).get(key)
        if val: valores.append((val, "BLOQUE_EMISOR"))
        
    # Receptor
    for key in ['ruc_dni', 'razon_social']:
        val = gt_dict.get('receptor', {}).get(key)
        if val: valores.append((val, "BLOQUE_RECEPTOR"))
        
    # Montos
    for key in ['subtotal', 'igv', 'total']:
        val = gt_dict.get('montos', {}).get(key)
        if val: valores.append((val, "BLOQUE_MONTOS"))
        
    return valores

def clasificar_linea(linea, valores_gt):
    """Asigna una clase a la línea OCR comparándola contra el Ground Truth usando Fuzzy Matching."""
    linea_limpia = str(linea).strip().lower()
    
    mejor_ratio = 0
    mejor_clase = "OTROS"
    
    for val_esperado, clase in valores_gt:
        val_esperado_limpio = str(val_esperado).strip().lower()
        
        # Primero, intentar match exacto o contención
        if val_esperado_limpio in linea_limpia:
            return clase
            
        # Si no, usar lógica difusa (Fuzzy Matching)
        ratio = difflib.SequenceMatcher(None, val_esperado_limpio, linea_limpia).ratio()
        
        # También comparamos contra cada token de la línea si la línea es muy larga
        tokens = linea_limpia.split()
        for token in tokens:
            token_ratio = difflib.SequenceMatcher(None, val_esperado_limpio, token).ratio()
            if token_ratio > ratio:
                ratio = token_ratio
        
        if ratio > mejor_ratio:
            mejor_ratio = ratio
            mejor_clase = clase
            
    # Umbral de similitud difusa (80%)
    if mejor_ratio >= 0.80:
        return mejor_clase
        
    return "OTROS"

def generar_dataset():
    dataset_dir = "test/images"
    ground_truth_path = "test/dataset/extraccion.json"
    output_csv = "labeled_dataset.csv"
    
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)
        
    archivos = [f for f in os.listdir(dataset_dir) if f in ground_truth]
    total_archivos = len(archivos)
    
    print(f"Iniciando Auto-Labeling (Fuzzy Matching) para {total_archivos} documentos...")
    
    dataset = []
    
    for i, filename in enumerate(archivos):
        file_path = os.path.join(dataset_dir, filename)
        gt_data = ground_truth[filename]
        valores_gt = aplanar_ground_truth(gt_data)
        
        try:
            lineas_ocr = obtener_lineas_ocr(file_path)
            for linea in lineas_ocr:
                clase = clasificar_linea(linea, valores_gt)
                dataset.append({
                    "texto": str(linea).strip(),
                    "clase_bloque": clase
                })
        except Exception as e:
            print(f"Error procesando {filename}: {e}")
            
        print(f"[{i+1}/{total_archivos}] {filename} procesado.")
        
    # Escribir CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["texto", "clase_bloque"])
        writer.writeheader()
        writer.writerows(dataset)
        
    print(f"\n¡Dataset generado exitosamente! Total de líneas etiquetadas: {len(dataset)}")
    print(f"Guardado en: {output_csv}")

if __name__ == "__main__":
    generar_dataset()
