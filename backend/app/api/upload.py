import os
import time
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

def _calcular_metricas(data: dict, elapsed: float) -> dict:
    """Calcula métricas automáticas sobre el resultado del pipeline."""
    # Todos los posibles campos ConfidenceField del modelo
    campos_flat = [
        data.get("comprobante", {}).get("tipo"),
        data.get("comprobante", {}).get("serie_numero"),
        data.get("comprobante", {}).get("fecha_emision"),
        data.get("comprobante", {}).get("moneda"),
        data.get("emisor", {}).get("ruc"),
        data.get("emisor", {}).get("razon_social"),
        data.get("receptor", {}).get("ruc_dni"),
        data.get("receptor", {}).get("razon_social"),
        data.get("montos", {}).get("subtotal"),
        data.get("montos", {}).get("igv"),
        data.get("montos", {}).get("total"),
    ]

    total_campos = len(campos_flat)
    
    # Campo detectado = tiene valor no nulo y no es "No detectado"
    detectados = [
        f for f in campos_flat
        if f and f.get("valor") not in (None, "No detectado", 0, 0.0)
    ]
    campos_detectados = len(detectados)

    # Score promedio de los campos detectados
    scores = [f["score"] for f in detectados if "score" in f]
    score_promedio = round(sum(scores) / len(scores)) if scores else 0

    return {
        "tiempo_procesamiento": round(elapsed, 2),
        "campos_detectados": campos_detectados,
        "total_campos": total_campos,
        "score_promedio": score_promedio,
    }


@router.post("/extract", response_model=InvoiceResponse)
async def upload_and_extract(file: UploadFile = File(...)):
    """
    Recibe un archivo (PDF, PNG, JPG), lo guarda temporalmente,
    y ejecuta el Pipeline V3 por Capas (OCR -> Clean -> Extract -> Validate).
    Devuelve el resultado enriquecido con métricas automáticas.
    """
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["pdf", "png", "jpg", "jpeg"]:
        raise HTTPException(status_code=400, detail="Formato no soportado.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name

    t_inicio = time.perf_counter()

    try:
        # FASE 0: Visión Computacional y OCR
        raw_text = process_document(temp_path)

        # FASE 1: Limpieza del OCR
        cleaned_text = clean_ocr_text(raw_text)

        # FASE 2 y 4: Extracción y Fallbacks
        extracted_data = parse_invoice(cleaned_text)

        # FASE 3 y 5: Validación y Post-procesamiento
        final_data = clean_extracted_data(extracted_data)

        # FASE 6: Métricas automáticas
        elapsed = time.perf_counter() - t_inicio
        final_data["metricas"] = _calcular_metricas(final_data, elapsed)

        logger.info(
            f"Pipeline completado en {final_data['metricas']['tiempo_procesamiento']}s | "
            f"Campos: {final_data['metricas']['campos_detectados']}/{final_data['metricas']['total_campos']} | "
            f"Score promedio: {final_data['metricas']['score_promedio']}%"
        )

        return final_data

    except Exception as e:
        logger.error(f"Error en el pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
