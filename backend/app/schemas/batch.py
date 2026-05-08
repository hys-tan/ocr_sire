from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.invoice import InvoiceResponse

class BatchItemResult(BaseModel):
    """Resultado individual de un documento dentro del lote."""
    archivo: str = Field(..., description="Nombre original del archivo")
    estado: str  = Field(..., description="completado | revision | error")
    datos: Optional[InvoiceResponse] = Field(None, description="Resultado OCR si el procesamiento fue exitoso")
    error: Optional[str] = Field(None, description="Mensaje de error si el procesamiento falló")

class BatchResponse(BaseModel):
    """Respuesta completa del endpoint de procesamiento por lotes."""
    total: int = Field(..., description="Total de archivos recibidos")
    procesados: int = Field(..., description="Archivos procesados correctamente")
    errores: int = Field(..., description="Archivos que fallaron")
    resultados: list[BatchItemResult]
