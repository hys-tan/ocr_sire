import os
import json
import csv
import time
import logging
from pathlib import Path

# Ajustar el path para poder importar los modulos de app
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.ocr_service import process_document
from app.services.cleaning_service import clean_ocr_text
from app.services.extraction_service import parse_invoice
from app.services.validation_service import clean_extracted_data

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compare_values(expected, extracted):
    """
    Compara dos valores normalizándolos (quita espacios y mayúsculas).
    Retorna 1 si coinciden (al menos parcialmente), 0 si no.
    """
    if not expected or not extracted:
        return 0
    
    exp = str(expected).lower().replace(" ", "").replace(",", "")
    ext = str(extracted).lower().replace(" ", "").replace(",", "")
    
    # Consideramos correcto si el valor esperado está dentro de lo extraído,
    # o si son idénticos.
    if exp in ext or ext in exp:
        return 1
    return 0

def evaluate_metrics():
    base_dir = os.path.dirname(__file__)
    # La carpeta está en 'test/dataset' y no en 'tests/dataset'
    dataset_dir = os.path.abspath(os.path.join(base_dir, "..", "test", "dataset"))
    images_dir = os.path.abspath(os.path.join(base_dir, "..", "test", "images"))
    json_path = os.path.join(dataset_dir, "extraccion.json")
    output_csv = os.path.join(dataset_dir, "metrics_paddleocr_base.csv")

    if not os.path.exists(json_path):
        logger.error(f"No se encontró el archivo JSON en: {json_path}")
        return

    if not os.path.exists(images_dir):
        logger.error(f"No se encontró la carpeta de imágenes en: {images_dir}")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)

    resultados = []
    
    # Campos que evaluaremos
    campos_evaluar = [
        ("comprobante", "tipo"),
        ("comprobante", "serie"),
        ("comprobante", "numero"),
        ("comprobante", "fecha_emision"),
        ("comprobante", "moneda"),
        ("emisor", "ruc"),
        ("emisor", "razon_social"),
        ("receptor", "ruc_dni"),
        ("receptor", "razon_social"),
        ("montos", "subtotal"),
        ("montos", "igv"),
        ("montos", "total")
    ]

    total_facturas = 0
    total_aciertos_global = 0
    total_campos_global = 0

    # Métricas detalladas
    metricas_por_calidad = {}
    metricas_por_campo = {
        f"{c[0]}_{c[1]}": {"aciertos_global": 0, "total_global": 0, "por_calidad": {}} 
        for c in campos_evaluar
    }

    for filename, expected_data in ground_truth.items():
        image_path = os.path.join(images_dir, filename)
        
        if not os.path.exists(image_path):
            logger.warning(f"No se encontró la imagen {filename}, omitiendo...")
            continue
            
        logger.info(f"Procesando: {filename} con PaddleOCR puro...")
        
        try:
            # 1. OCR (Solo PaddleOCR en esta rama)
            ocr_res = process_document(image_path)
            raw_text = ocr_res["text"]
            word_confidences = ocr_res.get("word_confidences", {})
            
            # 2. Pipeline de Extracción (Prototipo local, SIN Gemini)
            cleaned_text = clean_ocr_text(raw_text)
            extracted_data = parse_invoice(cleaned_text, word_confidences=word_confidences)
            final_data = clean_extracted_data(extracted_data)
            
            # 3. Comparación
            aciertos_factura = 0
            calidad = expected_data.get("calidad", "no_definida")
            
            if calidad not in metricas_por_calidad:
                metricas_por_calidad[calidad] = {"aciertos": 0, "total": 0, "facturas": 0}
            metricas_por_calidad[calidad]["facturas"] += 1
            
            fila_resultado = {
                "Archivo": filename,
                "Motor": "PaddleOCR Base",
                "Calidad": calidad
            }
            
            for categoria, campo in campos_evaluar:
                valor_esperado = expected_data.get(categoria, {}).get(campo, "")
                valor_extraido = final_data.get(categoria, {}).get(campo, "")
                
                acierto = compare_values(valor_esperado, valor_extraido)
                aciertos_factura += acierto
                
                # Guardamos 1 o 0 en el CSV
                nombre_columna = f"{categoria}_{campo}"
                fila_resultado[nombre_columna] = acierto
                
                # Tracker por campo (Global y Cruzado)
                metricas_por_campo[nombre_columna]["aciertos_global"] += acierto
                metricas_por_campo[nombre_columna]["total_global"] += 1
                
                if calidad not in metricas_por_campo[nombre_columna]["por_calidad"]:
                    metricas_por_campo[nombre_columna]["por_calidad"][calidad] = {"aciertos": 0, "total": 0}
                metricas_por_campo[nombre_columna]["por_calidad"][calidad]["aciertos"] += acierto
                metricas_por_campo[nombre_columna]["por_calidad"][calidad]["total"] += 1
                
            precision_factura = (aciertos_factura / len(campos_evaluar)) * 100
            fila_resultado["Precision_Global_Porcentaje"] = round(precision_factura, 2)
            
            resultados.append(fila_resultado)
            
            total_aciertos_global += aciertos_factura
            total_campos_global += len(campos_evaluar)
            total_facturas += 1
            
            metricas_por_calidad[calidad]["aciertos"] += aciertos_factura
            metricas_por_calidad[calidad]["total"] += len(campos_evaluar)
            
        except Exception as e:
            logger.error(f"Error procesando {filename}: {e}")

    # Guardar en CSV
    if resultados:
        fieldnames = ["Archivo", "Motor", "Calidad", "Precision_Global_Porcentaje"] + [f"{c[0]}_{c[1]}" for c in campos_evaluar]
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(resultados)
            
        precision_total = (total_aciertos_global / total_campos_global) * 100 if total_campos_global > 0 else 0
        
        # Re-abrir para añadir fila de promedios al final
        with open(output_csv, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            fila_promedios = {
                "Archivo": "PROMEDIO_GLOBAL",
                "Motor": "PaddleOCR Base",
                "Calidad": "-",
                "Precision_Global_Porcentaje": round(precision_total, 2)
            }
            for campo, stats in metricas_por_campo.items():
                if stats["total_global"] > 0:
                    fila_promedios[campo] = round((stats["aciertos_global"] / stats["total_global"]) * 100, 2)
                else:
                    fila_promedios[campo] = 0.0
            
            writer.writerow(fila_promedios)
            
        print(f"\n==================================================")
        print(f"MÉTRICAS FINALIZADAS PARA PADDLEOCR BASE")
        print(f"Facturas evaluadas: {total_facturas}")
        print(f"Precisión Global del Motor: {precision_total:.2f}%")
        print(f"Resultados guardados en: {output_csv}")
        print(f"==================================================\n")

        # Guardar reporte en Markdown
        md_path = os.path.join(dataset_dir, "global_metrics_paddleocr_base.md")
        with open(md_path, 'w', encoding='utf-8') as md:
            md.write("# Reporte de Métricas: PaddleOCR Base\n\n")
            md.write(f"- **Motor:** PaddleOCR puro (Sin OpenCV ni Tesseract)\n")
            md.write(f"- **Facturas evaluadas:** {total_facturas}\n")
            md.write(f"- **Total de campos evaluados:** {total_campos_global}\n")
            md.write(f"- **Total de aciertos exactos:** {total_aciertos_global}\n")
            md.write(f"- **Precisión Global:** `{precision_total:.2f}%`\n\n")
            
            md.write("## Precisión por Calidad del Documento\n")
            for cal, stats in metricas_por_calidad.items():
                if stats["total"] > 0:
                    prec_cal = (stats["aciertos"] / stats["total"]) * 100
                    md.write(f"- **Calidad '{cal}':** `{prec_cal:.2f}%` ({stats['facturas']} facturas)\n")
            md.write("\n")
            
            md.write("## Precisión por Campo de Datos (Matriz Cruzada)\n")
            calidades_detectadas = sorted(list(metricas_por_calidad.keys()))
            
            # Encabezado de la tabla
            headers = ["Campo de Dato", "Global"] + [f"Calidad '{c}'" for c in calidades_detectadas]
            md.write("| " + " | ".join(headers) + " |\n")
            md.write("|" + "|".join([":---"] * len(headers)) + "|\n")
            
            for campo, stats in metricas_por_campo.items():
                if stats["total_global"] > 0:
                    prec_global = (stats["aciertos_global"] / stats["total_global"]) * 100
                    fila = [f"**{campo}**", f"`{prec_global:.2f}%`"]
                    
                    for cal in calidades_detectadas:
                        if cal in stats["por_calidad"] and stats["por_calidad"][cal]["total"] > 0:
                            prec_calidad = (stats["por_calidad"][cal]["aciertos"] / stats["por_calidad"][cal]["total"]) * 100
                            fila.append(f"`{prec_calidad:.2f}%`")
                        else:
                            fila.append("`-`")
                    
                    md.write("| " + " | ".join(fila) + " |\n")
            md.write("\n")
            
            md.write(f"Los detalles por factura están guardados en: `metrics_paddleocr_base.csv`\n")
        print(f"Reporte visual guardado en: {md_path}\n")
    else:
        logger.warning("No se procesó ninguna factura. Revisa las rutas.")

if __name__ == "__main__":
    evaluate_metrics()
