import axios from 'axios';
import type { InvoiceResponse } from '../types/invoice';

// ─── Tipos del batch (espejo liviano del backend) ─────────────────────────────

export interface BatchItemResult {
  archivo: string;
  estado: 'completado' | 'revision' | 'error';
  datos?: InvoiceResponse;
  error?: string;
}

export interface BatchResponse {
  total: number;
  procesados: number;
  errores: number;
  resultados: BatchItemResult[];
}

// ─── Instancia Axios ──────────────────────────────────────────────────────────

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: { 'Accept': 'application/json' },
});

// ─── Endpoints ────────────────────────────────────────────────────────────────

/** Procesa un único documento (modo individual) */
export const extractInvoiceData = async (file: File): Promise<InvoiceResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  try {
    const response = await api.post<InvoiceResponse>('/api/v1/extract', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  } catch (error) {
    console.error('Error al comunicarse con el OCR:', error);
    throw error;
  }
};

/** Procesa un lote de documentos secuencialmente en el backend */
export const extractBatchData = async (files: File[]): Promise<BatchResponse> => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));
  try {
    const response = await api.post<BatchResponse>('/api/v1/extract-batch', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      // Timeout mayor para lotes grandes (40s)
      timeout: 40_000,
    });
    return response.data;
  } catch (error) {
    console.error('Error en el procesamiento por lote:', error);
    throw error;
  }
};
