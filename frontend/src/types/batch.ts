// ─── Tipos del sistema Batch OCR ─────────────────────────────────────────────

export type BatchStatus =
  | "pendiente"
  | "procesando"
  | "completado"
  | "revision"   // score global < 55%
  | "error";

export interface BatchFile {
  /** ID único generado en el cliente (crypto.randomUUID) */
  id: string;
  /** Archivo original del usuario */
  file: File;
  /** Estado actual en el pipeline */
  status: BatchStatus;
  /** Resultado de la extracción OCR (disponible cuando status = "completado" | "revision") */
  result?: import('./invoice').InvoiceResponse;
  /** Mensaje de error legible (disponible cuando status = "error") */
  error?: string;
}

// ─── Constantes de límites (fuente única de verdad para el frontend) ──────────

export const BATCH_LIMITS = {
  MAX_FILES:          10,
  MAX_SIZE_PER_FILE:  10 * 1024 * 1024,   // 10 MB en bytes
  MAX_TOTAL_SIZE:     50 * 1024 * 1024,   // 50 MB en bytes
  ACCEPTED_TYPES:     ["application/pdf", "image/png", "image/jpeg"],
  ACCEPTED_LABEL:     "PDF, PNG o JPG",
} as const;

// ─── Helpers de validación ────────────────────────────────────────────────────

export interface ValidationError {
  file?: string;   // nombre del archivo causante, si aplica
  message: string;
}

/**
 * Valida un array de archivos contra los límites definidos.
 * Devuelve un array de errores (vacío = sin errores).
 */
export function validateBatch(files: File[]): ValidationError[] {
  const errors: ValidationError[] = [];

  if (files.length > BATCH_LIMITS.MAX_FILES) {
    errors.push({ message: `Máximo ${BATCH_LIMITS.MAX_FILES} archivos por lote (seleccionaste ${files.length}).` });
  }

  let totalSize = 0;

  for (const file of files) {
    if (!(BATCH_LIMITS.ACCEPTED_TYPES as readonly string[]).includes(file.type)) {
      errors.push({ file: file.name, message: `"${file.name}" no es un formato soportado (${BATCH_LIMITS.ACCEPTED_LABEL}).` });
    }
    if (file.size > BATCH_LIMITS.MAX_SIZE_PER_FILE) {
      errors.push({ file: file.name, message: `"${file.name}" supera el límite de 10 MB (${(file.size / 1024 / 1024).toFixed(1)} MB).` });
    }
    totalSize += file.size;
  }

  if (totalSize > BATCH_LIMITS.MAX_TOTAL_SIZE) {
    errors.push({ message: `El lote completo supera los 50 MB (${(totalSize / 1024 / 1024).toFixed(1)} MB).` });
  }

  return errors;
}

/** Convierte bytes a string legible (MB con 1 decimal) */
export function formatMB(bytes: number): string {
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
