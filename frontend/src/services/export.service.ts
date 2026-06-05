/**
 * Servicio de Exportación de Datos OCR
 * ======================================
 * Genera archivos Excel (.xlsx) y CSV con los datos validados del lote.
 * Prioriza (en este orden): edición manual > valor_normalizado > valor OCR.
 *
 * Nunca envía datos al servidor — todo ocurre en el navegador.
 */
import * as XLSX from 'xlsx';
import type { BatchFile } from '../types/batch';
import type { ConfidenceField } from '../types/invoice';

// ─── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Resuelve el valor final de un campo, respetando la jerarquía:
 * 1. Corrección manual del usuario (editedValues)
 * 2. Valor normalizado por el backend
 * 3. Valor crudo del OCR
 */
function resolveValue(
  field: ConfidenceField<any> | undefined | null,
  fieldKey: string,
  editedValues: Record<string, string>
): string | number | null {
  if (!field) return null;

  // 1. Corrección manual
  if (fieldKey in editedValues) {
    const manual = editedValues[fieldKey];
    // Si es numérico, convertir
    const asNum = Number(manual.replace(',', '.'));
    return isNaN(asNum) ? manual : asNum;
  }

  // 2. Valor normalizado
  if (field.valor_normalizado !== undefined && field.valor_normalizado !== null) {
    return field.valor_normalizado;
  }

  // 3. Valor OCR crudo
  return field.valor ?? null;
}

// ─── Tipos de fila ────────────────────────────────────────────────────────────

export interface ExportRow {
  '#': number;
  'Archivo': string;
  'Tipo Comprobante': string | null;
  'Serie': string | null;
  'N° Comprobante (OCR)': string | null;
  'N° Comprobante (SUNAT)': string | null;
  'N° Advertencia': string | null;
  'Fecha Emisión': string | null;
  'Moneda': string | null;
  'RUC Emisor': string | null;
  'Razón Social Emisor': string | null;
  'RUC/DNI Receptor': string | null;
  'Razón Social Receptor': string | null;
  'Subtotal': number | null;
  'IGV': number | null;
  'Total': number | null;
  'Score OCR (%)': number;
  'Campos Editados': number;
  'Estado': string;
}

// ─── Función principal ────────────────────────────────────────────────────────

/**
 * Construye un array de filas exportables desde el estado del lote.
 * Solo incluye archivos que fueron procesados (con o sin error).
 */
export function buildExportRows(files: BatchFile[]): ExportRow[] {
  return files.map((batchFile, idx) => {
    const d = batchFile.result;
    const ev = batchFile.editedValues ?? {};
    const hasResult = d !== undefined;

    if (!hasResult) {
      return {
        '#': idx + 1,
        'Archivo': batchFile.file.name,
        'Tipo Comprobante': null,
        'Serie': null,
        'N° Comprobante (OCR)': null,
        'N° Comprobante (SUNAT)': null,
        'N° Advertencia': null,
        'Fecha Emisión': null,
        'Moneda': null,
        'RUC Emisor': null,
        'Razón Social Emisor': null,
        'RUC/DNI Receptor': null,
        'Razón Social Receptor': null,
        'Subtotal': null,
        'IGV': null,
        'Total': null,
        'Score OCR (%)': 0,
        'Campos Editados': 0,
        'Estado': 'Error: ' + (batchFile.error ?? 'desconocido'),
      };
    }

    const resolve = (field: ConfidenceField<any> | undefined | null, key: string) =>
      resolveValue(field, key, ev);

    return {
      '#': idx + 1,
      'Archivo': batchFile.file.name,
      'Tipo Comprobante': resolve(d.comprobante.tipo,         'comprobante.tipo')          as string | null,
      'Serie':            resolve(d.comprobante.serie,        'comprobante.serie')         as string | null,
      'N° Comprobante (OCR)': resolve(d.comprobante.numero,  'comprobante.numero')        as string | null,
      'N° Comprobante (SUNAT)': d.comprobante.numero_sunat ?? null,
      'N° Advertencia': d.comprobante.numero_sunat_advertencia ?? null,
      'Fecha Emisión':    resolve(d.comprobante.fecha_emision,'comprobante.fecha_emision') as string | null,
      'Moneda':           resolve(d.comprobante.moneda,       'comprobante.moneda')        as string | null,
      'RUC Emisor':       resolve(d.emisor.ruc,               'emisor.ruc')                as string | null,
      'Razón Social Emisor': resolve(d.emisor.razon_social,  'emisor.razon_social')       as string | null,
      'RUC/DNI Receptor': resolve(d.receptor.ruc_dni,        'receptor.ruc_dni')          as string | null,
      'Razón Social Receptor': resolve(d.receptor.razon_social,'receptor.razon_social')   as string | null,
      'Subtotal':         resolve(d.montos.subtotal,          'montos.subtotal')           as number | null,
      'IGV':              resolve(d.montos.igv,               'montos.igv')                as number | null,
      'Total':            resolve(d.montos.total,             'montos.total')              as number | null,
      'Score OCR (%)':    d.metricas?.score_promedio ?? 0,
      'Campos Editados':  Object.keys(ev).length,
      'Estado':           batchFile.status === 'completado' ? 'Completado'
                        : batchFile.status === 'revision'   ? 'Revisión pendiente'
                        : 'Error',
    };
  });
}

// ─── Exportar a Excel ─────────────────────────────────────────────────────────

/**
 * Descarga un archivo .xlsx con los datos validados del lote.
 * El archivo se llama: OCR_SIRE_<timestamp>.xlsx
 */
export function exportToExcel(files: BatchFile[]): void {
  const rows = buildExportRows(files);

  const ws = XLSX.utils.json_to_sheet(rows);

  // Anchos de columna orientativos
  ws['!cols'] = [
    { wch: 4  },  // #
    { wch: 28 },  // Archivo
    { wch: 24 },  // Tipo Comprobante
    { wch: 10 },  // Serie
    { wch: 20 },  // N° Comprobante (OCR)
    { wch: 20 },  // N° Comprobante (SUNAT)
    { wch: 32 },  // N° Advertencia
    { wch: 14 },  // Fecha Emisión
    { wch: 8  },  // Moneda
    { wch: 14 },  // RUC Emisor
    { wch: 30 },  // Razón Social Emisor
    { wch: 14 },  // RUC/DNI Receptor
    { wch: 30 },  // Razón Social Receptor
    { wch: 12 },  // Subtotal
    { wch: 10 },  // IGV
    { wch: 12 },  // Total
    { wch: 14 },  // Score OCR (%)
    { wch: 14 },  // Campos Editados
    { wch: 20 },  // Estado
  ];

  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Facturas');

  const timestamp = new Date().toISOString().slice(0, 16).replace('T', '_').replace(':', '-');
  XLSX.writeFile(wb, `OCR_SIRE_${timestamp}.xlsx`);
}

// ─── Exportar a TXT ───────────────────────────────────────────────────────────

/**
 * Descarga un archivo .txt con un reporte legible por humanos.
 * Útil para imprimir o adjuntar en informes.
 */
export function exportToTXT(files: BatchFile[]): void {
  const rows = buildExportRows(files);
  const now = new Date().toLocaleString('es-PE', { dateStyle: 'long', timeStyle: 'short' });

  const lines: string[] = [
    '╔════════════════════════════════════════════════════════════╗',
    '║            OCR SIRE — Reporte de Lote                      ║',
    '╚════════════════════════════════════════════════════════════╝',
    `  Fecha de exportación : ${now}`,
    `  Total de documentos  : ${files.length}`,
    `  Procesados con éxito : ${files.filter(f => f.status === 'completado' || f.status === 'revision').length}`,
    `  Con errores          : ${files.filter(f => f.status === 'error').length}`,
    '',
    '════════════════════════════════════════════════════════════',
    '',
  ];

  rows.forEach((row, idx) => {
    lines.push(`── Documento ${idx + 1}: ${row['Archivo']}`);
    lines.push(`   Estado              : ${row['Estado']}`);
    lines.push(`   Score OCR           : ${row['Score OCR (%)']}%`);
    lines.push(`   Campos editados     : ${row['Campos Editados']}`);
    lines.push('');
    lines.push(`   Tipo comprobante   : ${row['Tipo Comprobante'] ?? '—'}`);
    lines.push(`   Serie              : ${row['Serie'] ?? '—'}`);
    lines.push(`   N° Comprobante (OCR)  : ${row['N° Comprobante (OCR)'] ?? '—'}`);
    lines.push(`   N° Comprobante (SUNAT): ${row['N° Comprobante (SUNAT)'] ?? '—'}`);
    if (row['N° Advertencia']) {
      lines.push(`   ⚠ Advertencia N°     : ${row['N° Advertencia']}`);
    }
    lines.push(`   Fecha de emisión   : ${row['Fecha Emisión'] ?? '—'}`);
    lines.push(`   Moneda             : ${row['Moneda'] ?? '—'}`);
    lines.push('');
    lines.push(`   RUC Emisor         : ${row['RUC Emisor'] ?? '—'}`);
    lines.push(`   Razón Social Emis. : ${row['Razón Social Emisor'] ?? '—'}`);
    lines.push(`   RUC/DNI Receptor   : ${row['RUC/DNI Receptor'] ?? '—'}`);
    lines.push(`   Razón Social Rec.  : ${row['Razón Social Receptor'] ?? '—'}`);
    lines.push('');
    lines.push(`   Subtotal           : ${row['Subtotal'] != null ? `S/ ${Number(row['Subtotal']).toFixed(2)}` : '—'}`);
    lines.push(`   IGV (18%)          : ${row['IGV'] != null ? `S/ ${Number(row['IGV']).toFixed(2)}` : '—'}`);
    lines.push(`   Total              : ${row['Total'] != null ? `S/ ${Number(row['Total']).toFixed(2)}` : '—'}`);
    lines.push('');
    lines.push('────────────────────────────────────────────────────────────');
    lines.push('');
  });

  lines.push('  Reporte generado por OCR SIRE');

  const blob = new Blob([lines.join('\r\n')], { type: 'text/plain;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  const timestamp = new Date().toISOString().slice(0, 16).replace('T', '_').replace(':', '-');
  a.href     = url;
  a.download = `OCR_SIRE_${timestamp}.txt`;
  a.click();
  URL.revokeObjectURL(url);
}

/**
 * Descarga un archivo .csv con los datos validados del lote.
 * Separador: punto y coma (compatible con Excel en español).
 */
export function exportToCSV(files: BatchFile[]): void {
  const rows = buildExportRows(files);
  if (rows.length === 0) return;

  const headers = Object.keys(rows[0]) as (keyof ExportRow)[];
  const sep = ';';

  const csvLines = [
    headers.join(sep),
    ...rows.map(row =>
      headers.map(h => {
        const val = row[h];
        if (val === null || val === undefined) return '';
        // Escapar comas y comillas dentro del valor
        const str = String(val);
        return str.includes(sep) || str.includes('"') || str.includes('\n')
          ? `"${str.replace(/"/g, '""')}"`
          : str;
      }).join(sep)
    ),
  ];

  const blob = new Blob(['\uFEFF' + csvLines.join('\r\n')], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  const timestamp = new Date().toISOString().slice(0, 16).replace('T', '_').replace(':', '-');
  a.href     = url;
  a.download = `OCR_SIRE_${timestamp}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
