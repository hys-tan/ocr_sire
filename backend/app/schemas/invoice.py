from pydantic import BaseModel, Field
from typing import Optional, Any

class ConfidenceField(BaseModel):
    valor: Any
    confianza: str = Field(..., description="ALTA, MEDIA o BAJA")
    estrategia: str = Field(..., description="Estrategia usada para la extracción")

class ComprobanteBase(BaseModel):
    tipo: Optional[ConfidenceField] = Field(None, description="Factura Electrónica, Boleta, etc.")
    serie_numero: Optional[ConfidenceField] = Field(None, description="Ej: F001-0083104")
    fecha_emision: Optional[ConfidenceField] = Field(None, description="DD/MM/YYYY")
    moneda: Optional[ConfidenceField] = Field(None, description="PEN o USD")

class EmisorBase(BaseModel):
    ruc: Optional[ConfidenceField] = Field(None, description="RUC de 11 dígitos")
    razon_social: Optional[ConfidenceField] = Field(None)

class ReceptorBase(BaseModel):
    ruc_dni: Optional[str] = Field(None)
    razon_social: Optional[ConfidenceField] = Field(None)

class MontosBase(BaseModel):
    subtotal: Optional[ConfidenceField] = Field(None)
    igv: Optional[ConfidenceField] = Field(None)
    total: Optional[ConfidenceField] = Field(None)

class InvoiceResponse(BaseModel):
    """Modelo principal de respuesta que la API enviará al Frontend."""
    comprobante: ComprobanteBase
    emisor: EmisorBase
    receptor: ReceptorBase
    montos: MontosBase
