import axios from 'axios';
import type { InvoiceResponse } from '../types/invoice';

// Instancia configurada de Axios
export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Accept': 'application/json',
  },
});

// Función para subir y procesar el documento
export const extractInvoiceData = async (file: File): Promise<InvoiceResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await api.post<InvoiceResponse>('/api/v1/extract', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    console.error('Error al comunicarse con el OCR:', error);
    throw error;
  }
};
