import os
import tempfile
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException

from app.services.ocr_service import process_document
from app.services.cleaning_service import clean_ocr_text
from app.services.extraction_service import parse_invoice
from app.services.validation_service import clean_extracted_data
from app.schemas.invoice import InvoiceResponse

router = APIRouter()
logger = logging.getLogger("ExtractorSIRE")

@router.post("/extract", response_model=InvoiceResponse)
async def upload_and_extract(file: UploadFile = File(...)):
    """
    Recibe un archivo (PDF, PNG, JPG), lo guarda temporalmente,
    y ejecuta el Pipeline V3 por Capas (OCR -> Clean -> Extract -> Validate).
    """
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "png", "jpg", "jpeg"]:
        raise HTTPException(status_code=400, detail="Formato no soportado.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        # FASE 0: Visión Computacional y OCR
        raw_text = process_document(temp_path)
        
        # FASE 1: Limpieza del OCR
        cleaned_text = clean_ocr_text(raw_text)
        
        # FASE 2 y 4: Extracción y Fallbacks
        extracted_data = parse_invoice(cleaned_text)
        
        # FASE 3 y 5: Validación y Post-procesamiento
        final_data = clean_extracted_data(extracted_data)
        
        return final_data

    except Exception as e:
        logger.error(f"Error en el pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
