export type ConfianzaNivel = "ALTA" | "MEDIA" | "BAJA";

export interface ConfidenceField<T = string | number | null> {
  valor: T;
  confianza: ConfianzaNivel;
  estrategia: string;
  score: number;
}

export interface Comprobante {
  tipo: ConfidenceField<string | null>;
  serie_numero: ConfidenceField<string | null>;
  fecha_emision: ConfidenceField<string | null>;
  moneda: ConfidenceField<string | null>;
}

export interface Emisor {
  ruc: ConfidenceField<string | null>;
  razon_social: ConfidenceField<string | null>;
}

export interface Receptor {
  ruc_dni: ConfidenceField<string | null>;
  razon_social: ConfidenceField<string | null>;
}

export interface Montos {
  subtotal: ConfidenceField<number>;
  igv: ConfidenceField<number>;
  total: ConfidenceField<number>;
}

export interface InvoiceResponse {
  comprobante: Comprobante;
  emisor: Emisor;
  receptor: Receptor;
  montos: Montos;
}
