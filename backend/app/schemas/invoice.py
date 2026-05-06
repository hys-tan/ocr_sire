from pydantic import BaseModel, Field
from typing import Optional

class ComprobanteBase(BaseModel):
    tipo: str = Field(..., description="Factura Electrónica, Boleta, etc.")
    serie_numero: Optional[str] = Field(None, description="Ej: F001-0083104")
    fecha_emision: Optional[str] = Field(None, description="DD/MM/YYYY")
    moneda: str = Field("PEN", description="PEN o USD")

class ConfidenceField(BaseModel):
    valor: str
    confianza: str = Field(..., description="ALTA, MEDIA o BAJA")
    estrategia: str = Field(..., description="Estrategia usada para la extracción")

class EmisorBase(BaseModel):
    ruc: Optional[str] = Field(None, description="RUC de 11 dígitos")
    razon_social: Optional[ConfidenceField] = Field(None)

class ReceptorBase(BaseModel):
    ruc_dni: Optional[str] = Field(None)
    razon_social: Optional[ConfidenceField] = Field(None)

class MontosBase(BaseModel):
    subtotal: float = Field(0.0)
    igv: float = Field(0.0)
    total: float = Field(0.0)

class InvoiceResponse(BaseModel):
    """Modelo principal de respuesta que la API enviará al Frontend."""
    comprobante: ComprobanteBase
    emisor: EmisorBase
    receptor: ReceptorBase
    montos: MontosBase
