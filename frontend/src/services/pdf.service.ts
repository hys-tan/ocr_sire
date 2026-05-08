import { PDFDocument } from 'pdf-lib';

/**
 * Lee un archivo PDF localmente y devuelve el número de páginas.
 *
 * No envía nada al servidor — todo el parsing ocurre en el navegador.
 *
 * @returns número de páginas (≥ 1), o lanza un error si el PDF es inválido.
 */
export async function getPdfPageCount(file: File): Promise<number> {
  const buffer = await file.arrayBuffer();
  const pdf    = await PDFDocument.load(buffer, {
    // Evitar que falle en PDFs con metadatos cifrados o con advertencias
    ignoreEncryption: true,
  });
  return pdf.getPageCount();
}

/**
 * Versión segura: nunca lanza, devuelve null si el PDF es ilegible.
 * Útil para mostrar feedback visual sin interrumpir el flujo.
 */
export async function tryGetPdfPageCount(file: File): Promise<number | null> {
  try {
    return await getPdfPageCount(file);
  } catch {
    return null;
  }
}

/**
 * Lee el conteo de páginas de un lote de archivos en paralelo.
 * Los no-PDF (imágenes) devuelven 1 directamente sin parsear.
 *
 * @returns Map<File, number | null> — null indica PDF ilegible/corrupto
 */
export async function getPageCountsForBatch(
  files: File[]
): Promise<Map<File, number | null>> {
  const results = await Promise.all(
    files.map(async file => {
      // Imágenes cuentan siempre como 1 página
      if (file.type.startsWith('image/')) return [file, 1] as const;
      const count = await tryGetPdfPageCount(file);
      return [file, count] as const;
    })
  );
  return new Map(results);
}
