import os
import pytest
from app.services.ocr_service import process_document
from app.services.cleaning_service import clean_ocr_text
from app.services.extraction_service import parse_invoice
from app.services.validation_service import clean_extracted_data
from app.core.comprobante_utils import get_serie_numero

# Obtener ruta absoluta del proyecto backend para poder cargar los assets de prueba
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _get_val(field):
    if field is None:
        return None
    if isinstance(field, dict):
        return field.get("valor_normalizado") or field.get("valor")
    return field

def test_ocr_pipeline_prueba2():
    """Prueba que el pipeline de OCR extrae y normaliza correctamente los datos de prueba2.pdf."""
    pdf_path = os.path.join(BACKEND_DIR, "assets", "prueba2.pdf")
    assert os.path.exists(pdf_path), f"El archivo de prueba no se encontró en: {pdf_path}"
    
    # 1. Ejecutar OCR y confianza nativa
    ocr_res = process_document(pdf_path)
    assert "text" in ocr_res
    assert "word_confidences" in ocr_res
    
    # 2. Limpieza
    cleaned = clean_ocr_text(ocr_res["text"])
    
    # 3. Extracción
    extracted = parse_invoice(cleaned, word_confidences=ocr_res["word_confidences"])
    
    # 4. Post-procesamiento y validación final
    final_data = clean_extracted_data(extracted)
    
    # Verificar campos clave contra el Ground Truth de prueba2.pdf
    tipo = _get_val(final_data["comprobante"].get("tipo"))
    assert tipo == "Factura Electrónica"
    
    serie_numero = get_serie_numero(final_data["comprobante"].get("serie"), final_data["comprobante"].get("numero"))
    assert serie_numero == "FFF1-000927"
    
    fecha = _get_val(final_data["comprobante"].get("fecha_emision"))
    assert fecha == "16/04/2024"
    
    emisor_ruc = _get_val(final_data["emisor"].get("ruc"))
    assert emisor_ruc == "20601842689"
    
    receptor_ruc = _get_val(final_data["receptor"].get("ruc_dni"))
    assert receptor_ruc == "20525058876"
    
    receptor_rs = _get_val(final_data["receptor"].get("razon_social"))
    assert receptor_rs == "Wm Import S.A.C."
    
    total = _get_val(final_data["montos"].get("total"))
    assert float(total) == 15900.00
