from pydantic import BaseModel, Field
from typing import Optional, Any

class ConfidenceField(BaseModel):
    valor: Any
    confianza: str = Field(..., description="ALTA, MEDIA o BAJA")
    estrategia: str = Field(..., description="Estrategia usada para la extracción")
    score: int = Field(default=0, ge=0, le=100, description="Score numérico de confianza 0-100")

class ComprobanteBase(BaseModel):
    tipo: Optional[ConfidenceField] = Field(None, description="Factura Electrónica, Boleta, etc.")
    serie_numero: Optional[ConfidenceField] = Field(None, description="Ej: F001-0083104")
    fecha_emision: Optional[ConfidenceField] = Field(None, description="DD/MM/YYYY")
    moneda: Optional[ConfidenceField] = Field(None, description="PEN o USD")

class EmisorBase(BaseModel):
    ruc: Optional[ConfidenceField] = Field(None, description="RUC de 11 dígitos")
    razon_social: Optional[ConfidenceField] = Field(None)

class ReceptorBase(BaseModel):
    ruc_dni: Optional[ConfidenceField] = Field(None)
    razon_social: Optional[ConfidenceField] = Field(None)

class MontosBase(BaseModel):
    subtotal: Optional[ConfidenceField] = Field(None)
    igv: Optional[ConfidenceField] = Field(None)
    total: Optional[ConfidenceField] = Field(None)

class MetricasOCR(BaseModel):
    """Métricas automáticas generadas por el pipeline de extracción."""
    tiempo_procesamiento: float = Field(..., description="Segundos totales del pipeline")
    campos_detectados: int = Field(..., description="Campos con valor no nulo")
    total_campos: int = Field(default=11, description="Total de campos del modelo")
    score_promedio: int = Field(..., description="Promedio de scores de todos los campos (0-100)")

class InvoiceResponse(BaseModel):
    """Modelo principal de respuesta que la API enviará al Frontend."""
    comprobante: ComprobanteBase
    emisor: EmisorBase
    receptor: ReceptorBase
    montos: MontosBase
    metricas: MetricasOCR
