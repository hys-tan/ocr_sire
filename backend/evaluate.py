import json
from app.services.ocr_service import process_document
from app.services.extraction_service import parse_invoice
from app.services.cleaning_service import clean_ocr_text
from app.services.validation_service import clean_extracted_data

def run_evaluation():
    """
    Fase 7: Evaluación y Métricas.
    Procesa un PDF/Imagen, pasa por todo el pipeline y compara contra la verdad (Ground Truth).
    """
    
    # 1. Define aquí tu archivo de prueba
    test_file = "assets/prueba2.pdf" 
    print(f"=== Procesando archivo: {test_file} ===")
    
    # 2. Define aquí los datos que TÚ SABES que son correctos (Ground Truth) para prueba2.pdf
    # ¡Si usas una factura diferente, DEBES actualizar estos valores manuales o la precisión será 0%!
    ground_truth = {
        "comprobante.tipo": "FACTURA ELECTRÓNICA",
        "comprobante.serie_numero": "FFF1-000927",
        "comprobante.fecha_emision": "16/04/2024",
        "emisor.ruc": "20601842689",
        "emisor.razon_social": "CORPORACION IMDICOR S.A.C.",
        "receptor.ruc_dni": "20525058876",
        "receptor.razon_social": "WM IMPORT S.A.C.",
        "montos.total": 15900.00
    }
    
    print("\nIniciando Pipeline V3...")
    
    # Ejecutar Pipeline V3 COMPLETO (¡No tienes que ejecutar archivo por archivo!)
    raw_text = process_document(test_file)            # FASE 0: OCR
    texto_limpio = clean_ocr_text(raw_text)           # FASE 1: Limpieza
    datos_extraidos = parse_invoice(texto_limpio)     # FASE 2 y 4: Extracción
    datos_finales = clean_extracted_data(datos_extraidos) # FASE 3 y 5: Validación
    
    # Aplanar diccionario extraído para comparar
    extracted_flat = {
        "comprobante.tipo": datos_finales["comprobante"]["tipo"],
        "comprobante.serie_numero": datos_finales["comprobante"]["serie_numero"],
        "comprobante.fecha_emision": datos_finales["comprobante"]["fecha_emision"],
        "emisor.ruc": datos_finales["emisor"]["ruc"],
        "emisor.razon_social": datos_finales["emisor"]["razon_social"]["valor"] if isinstance(datos_finales["emisor"]["razon_social"], dict) else datos_finales["emisor"]["razon_social"],
        "receptor.ruc_dni": datos_finales["receptor"]["ruc_dni"],
        "receptor.razon_social": datos_finales["receptor"]["razon_social"]["valor"] if isinstance(datos_finales["receptor"]["razon_social"], dict) else datos_finales["receptor"]["razon_social"],
        "montos.total": datos_finales["montos"]["total"],
    }
    
    aciertos = 0
    total = len(ground_truth)
    
    print("\n=== RESULTADOS DE EVALUACIÓN ===")
    for key, expected in ground_truth.items():
        actual = extracted_flat.get(key)
        
        # Comparación insensible a mayúsculas/minúsculas
        if str(actual).strip().upper() == str(expected).strip().upper():
            aciertos += 1
            print(f"[OK] {key}: {actual}")
        else:
            print(f"[ERROR] {key}")
            print(f"  Esperado: {expected}")
            print(f"  Obtenido: {actual}")
            
    precision = (aciertos / total) * 100
    print(f"\n=== MÉTRICAS FINALES ===")
    print(f"Precisión General: {precision:.2f}% ({aciertos}/{total} campos correctos)")

if __name__ == "__main__":
    run_evaluation()
