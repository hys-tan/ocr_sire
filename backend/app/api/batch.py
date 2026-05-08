import os
import time
import tempfile
import logging
from typing import List

from fastapi import APIRouter, File, UploadFile, HTTPException

from app.services.ocr_service import process_document
from app.services.cleaning_service import clean_ocr_text
from app.services.extraction_service import parse_invoice
from app.services.validation_service import clean_extracted_data
from app.schemas.batch import BatchResponse, BatchItemResult

router = APIRouter()
logger = logging.getLogger("ExtractorSIRE.Batch")

# ─── Límites del lote (espejo del frontend) ───────────────────────────────────
MAX_FILES        = 10
MAX_PAGES_PER_PDF = 5
MAX_PAGES_TOTAL  = 15
MAX_SIZE_PER_FILE = 10 * 1024 * 1024   # 10 MB
MAX_SIZE_TOTAL    = 50 * 1024 * 1024   # 50 MB
ACCEPTED_EXT      = {"pdf", "png", "jpg", "jpeg"}


def _contar_paginas_pdf(path: str) -> int:
    """Cuenta páginas usando PyMuPDF (fitz). Devuelve 1 para imágenes."""
    ext = path.rsplit(".", 1)[-1].lower()
    if ext in ("png", "jpg", "jpeg"):
        return 1
    try:
        import fitz
        doc = fitz.open(path)
        count = doc.page_count
        doc.close()
        return count
    except Exception:
        return -1   # PDF corrupto / ilegible


def _calcular_metricas(data: dict, elapsed: float) -> dict:
    """Reutiliza la misma lógica del endpoint individual."""
    campos_flat = [
        data.get("comprobante", {}).get("tipo"),
        data.get("comprobante", {}).get("serie"),
        data.get("comprobante", {}).get("numero"),
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
    detectados = [
        f for f in campos_flat
        if f and f.get("valor") not in (None, "No detectado", 0, 0.0)
    ]
    scores = [f["score"] for f in detectados if "score" in f]
    score_promedio = round(sum(scores) / len(scores)) if scores else 0
    return {
        "tiempo_procesamiento": round(elapsed, 2),
        "campos_detectados": len(detectados),
        "total_campos": total_campos,
        "score_promedio": score_promedio,
    }


@router.post("/extract-batch", response_model=BatchResponse)
async def extract_batch(files: List[UploadFile] = File(...)):
    """
    Recibe un lote de archivos (PDF/PNG/JPG), los valida y los procesa
    secuencialmente mediante el pipeline OCR.

    Validaciones backend (la fuente de verdad real):
    - Máx. 10 archivos
    - Máx. 10 MB por archivo
    - Máx. 50 MB total del lote
    - Máx. 5 páginas por PDF
    - Máx. 15 páginas totales del lote
    - Formato válido (PDF, PNG, JPG)
    - PDF legible (no corrupto)
    """
    if not files:
        raise HTTPException(status_code=400, detail="No se recibieron archivos.")

    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=422,
            detail=f"El lote supera el máximo de {MAX_FILES} archivos (recibidos: {len(files)})."
        )

    resultados: list[BatchItemResult] = []
    temp_paths: list[str] = []
    paginas_totales = 0

    # ── FASE 0: Guardar temporalmente y validar ────────────────────────────────
    saved: list[tuple[UploadFile, str]] = []

    for upload in files:
        ext = (upload.filename or "").rsplit(".", 1)[-1].lower()

        if ext not in ACCEPTED_EXT:
            resultados.append(BatchItemResult(
                archivo=upload.filename or "desconocido",
                estado="error",
                error=f"Formato no soportado: .{ext}. Use PDF, PNG o JPG."
            ))
            continue

        content = await upload.read()

        if len(content) > MAX_SIZE_PER_FILE:
            resultados.append(BatchItemResult(
                archivo=upload.filename or "desconocido",
                estado="error",
                error=f"El archivo supera 10 MB ({len(content) / 1024 / 1024:.1f} MB)."
            ))
            continue

        # Guardar en disco temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        temp_paths.append(tmp_path)

        # Contar páginas (solo para PDFs)
        paginas = _contar_paginas_pdf(tmp_path)

        if paginas == -1:
            resultados.append(BatchItemResult(
                archivo=upload.filename or "desconocido",
                estado="error",
                error="El archivo PDF está dañado o no es legible."
            ))
            os.remove(tmp_path)
            temp_paths.remove(tmp_path)
            continue

        if paginas > MAX_PAGES_PER_PDF:
            resultados.append(BatchItemResult(
                archivo=upload.filename or "desconocido",
                estado="error",
                error=f"El PDF supera el límite de {MAX_PAGES_PER_PDF} páginas ({paginas} páginas)."
            ))
            os.remove(tmp_path)
            temp_paths.remove(tmp_path)
            continue

        paginas_totales += paginas

        if paginas_totales > MAX_PAGES_TOTAL:
            resultados.append(BatchItemResult(
                archivo=upload.filename or "desconocido",
                estado="error",
                error=f"El lote supera el máximo de {MAX_PAGES_TOTAL} páginas totales."
            ))
            os.remove(tmp_path)
            temp_paths.remove(tmp_path)
            break

        saved.append((upload, tmp_path))

    # ── FASE 1: Procesar secuencialmente ──────────────────────────────────────
    for upload, tmp_path in saved:
        nombre = upload.filename or "desconocido"
        t_inicio = time.perf_counter()
        try:
            logger.info(f"[Batch] Procesando: {nombre}")
            raw_text    = process_document(tmp_path)
            cleaned     = clean_ocr_text(raw_text)
            extracted   = parse_invoice(cleaned)
            final_data  = clean_extracted_data(extracted)
            elapsed     = time.perf_counter() - t_inicio
            final_data["metricas"] = _calcular_metricas(final_data, elapsed)

            score = final_data["metricas"]["score_promedio"]
            estado = "revision" if score < 55 else "completado"

            resultados.append(BatchItemResult(
                archivo=nombre,
                estado=estado,
                datos=final_data,
            ))
            logger.info(f"[Batch] OK → {nombre} | Score: {score}% | {elapsed:.2f}s")

        except Exception as e:
            elapsed = time.perf_counter() - t_inicio
            logger.error(f"[Batch] Error en {nombre}: {e}")
            resultados.append(BatchItemResult(
                archivo=nombre,
                estado="error",
                error=str(e),
            ))
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    procesados = sum(1 for r in resultados if r.estado in ("completado", "revision"))
    errores    = sum(1 for r in resultados if r.estado == "error")

    logger.info(f"[Batch] Lote finalizado: {procesados} OK, {errores} errores")

    return BatchResponse(
        total=len(resultados),
        procesados=procesados,
        errores=errores,
        resultados=resultados,
    )
