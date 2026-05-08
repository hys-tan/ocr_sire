import React, { useCallback, useState, useRef } from 'react';
import { UploadCloud, FileText, X, Loader2, AlertCircle, CheckCircle2, FileX } from 'lucide-react';
import { validateBatch, formatMB, BATCH_LIMITS } from '../types/batch';
import { getPageCountsForBatch } from '../services/pdf.service';
import type { ValidationError } from '../types/batch';

interface UploadSectionProps {
  onFilesSelect: (files: File[]) => void;
  isLoading: boolean;
}

// Clave única por archivo (nombre + tamaño)
const fileKey = (f: File) => `${f.name}-${f.size}`;

export default function UploadSection({ onFilesSelect, isLoading }: UploadSectionProps) {
  const [isDragging, setIsDragging]             = useState(false);
  const [selectedFiles, setSelectedFiles]       = useState<File[]>([]);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [pageCounts, setPageCounts]             = useState<Map<string, number | null>>(new Map());
  const [isReadingPages, setIsReadingPages]     = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ─── Validación de páginas ───────────────────────────────────────────────────

  function buildPageErrors(files: File[], counts: Map<string, number | null>): ValidationError[] {
    const errors: ValidationError[] = [];
    let totalPages = 0;

    for (const file of files) {
      const pages = counts.get(fileKey(file));
      if (pages === null) {
        errors.push({ file: file.name, message: `"${file.name}" no se pudo leer — puede estar dañado o protegido.` });
        continue;
      }
      if (pages !== undefined) {
        if (pages > BATCH_LIMITS.MAX_PAGES_PER_FILE) {
          errors.push({ file: file.name, message: `"${file.name}" supera el límite de ${BATCH_LIMITS.MAX_PAGES_PER_FILE} páginas (tiene ${pages}).` });
        }
        totalPages += pages;
      }
    }

    if (totalPages > BATCH_LIMITS.MAX_PAGES_TOTAL) {
      errors.push({ message: `El lote supera el máximo de ${BATCH_LIMITS.MAX_PAGES_TOTAL} páginas totales (${totalPages} páginas).` });
    }
    return errors;
  }

  // ─── Lógica de archivos (ahora async por la lectura de páginas) ──────────────

  const processFiles = useCallback(async (incoming: FileList | null) => {
    if (!incoming || incoming.length === 0) return;

    const merged = Array.from(
      new Map(
        [...selectedFiles, ...Array.from(incoming)].map(f => [fileKey(f), f])
      ).values()
    );

    // Validaciones síncronas (tamaño, tipo, cantidad)
    const sizeErrors = validateBatch(merged);
    setValidationErrors(sizeErrors);
    setSelectedFiles(merged);

    // Leer páginas en background
    setIsReadingPages(true);
    try {
      const newCounts = await getPageCountsForBatch(merged);
      // Convertir claves File → string
      const stringCounts = new Map<string, number | null>(
        Array.from(newCounts.entries()).map(([f, n]) => [fileKey(f), n])
      );
      setPageCounts(stringCounts);

      const pageErrors = buildPageErrors(merged, stringCounts);
      setValidationErrors([...sizeErrors, ...pageErrors]);
    } finally {
      setIsReadingPages(false);
    }
  }, [selectedFiles]);

  const removeFile = (index: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const updated = selectedFiles.filter((_, i) => i !== index);
    const sizeErrors = validateBatch(updated);
    const pageErrors = buildPageErrors(updated, pageCounts);
    setValidationErrors([...sizeErrors, ...pageErrors]);
    setSelectedFiles(updated);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const clearAll = () => {
    setSelectedFiles([]);
    setValidationErrors([]);
    setPageCounts(new Map());
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleSubmit = () => {
    if (selectedFiles.length > 0 && validationErrors.length === 0 && !isLoading && !isReadingPages) {
      onFilesSelect(selectedFiles);
    }
  };

  // ─── Drag & Drop ─────────────────────────────────────────────────────────────

  const handleDragOver  = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragging(true);  }, []);
  const handleDragLeave = useCallback((e: React.DragEvent) => { e.preventDefault(); setIsDragging(false); }, []);
  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    processFiles(e.dataTransfer.files);
  }, [processFiles]);

  // ─── Métricas del lote ───────────────────────────────────────────────────────

  const totalSize  = selectedFiles.reduce((acc, f) => acc + f.size, 0);
  const fileCount  = selectedFiles.length;
  const hasErrors  = validationErrors.length > 0;
  const totalPages = Array.from(pageCounts.values()).reduce<number>((acc, n) => acc + (n ?? 0), 0);
  const canSubmit  = fileCount > 0 && !hasErrors && !isLoading && !isReadingPages;

  const pctFiles = Math.min((fileCount  / BATCH_LIMITS.MAX_FILES)      * 100, 100);
  const pctSize  = Math.min((totalSize  / BATCH_LIMITS.MAX_TOTAL_SIZE) * 100, 100);
  const pctPages = Math.min((totalPages / BATCH_LIMITS.MAX_PAGES_TOTAL) * 100, 100);

  // ─── UI ──────────────────────────────────────────────────────────────────────

  return (
    <div className="w-full max-w-2xl mx-auto mt-8 space-y-4">

      {/* Zona de drop */}
      <div
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ease-in-out
          ${isDragging        ? 'border-purple-500 bg-purple-50 scale-[1.01]' : ''}
          ${!isDragging && !hasErrors ? 'border-gray-300 hover:border-purple-400 hover:bg-gray-50' : ''}
          ${hasErrors         ? 'border-red-300 bg-red-50/30' : ''}
          ${isLoading         ? 'opacity-50 pointer-events-none' : 'cursor-pointer'}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={e => processFiles(e.target.files)}
          className="hidden"
          accept=".pdf,image/png,image/jpeg"
          multiple
        />
        <div className="flex flex-col items-center space-y-3">
          <div className={`p-4 rounded-full ${hasErrors ? 'bg-red-100 text-red-500' : 'bg-purple-100 text-purple-600'}`}>
            <UploadCloud size={36} />
          </div>
          <div>
            <p className="text-base font-semibold text-gray-700">Arrastra y suelta tus facturas aquí</p>
            <p className="text-sm text-gray-400 mt-1">
              Máx. {BATCH_LIMITS.MAX_FILES} archivos · {BATCH_LIMITS.MAX_PAGES_PER_FILE} pág/PDF · {BATCH_LIMITS.MAX_PAGES_TOTAL} pág. total · 10 MB/archivo
            </p>
          </div>
          <span className="text-xs px-4 py-1.5 bg-white border border-gray-200 rounded-full text-gray-600 hover:bg-gray-50 font-medium">
            Explorar archivos
          </span>
        </div>
      </div>

      {/* Errores de validación */}
      {hasErrors && (
        <div className="space-y-1.5">
          {validationErrors.map((err, i) => (
            <div key={i} className="flex items-start space-x-2 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              <AlertCircle size={15} className="flex-shrink-0 mt-0.5" />
              <span>{err.message}</span>
            </div>
          ))}
        </div>
      )}

      {/* Lista de archivos */}
      {fileCount > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">

          {/* Cabecera — contadores */}
          <div className="px-4 py-3 bg-gray-50 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="text-xs text-gray-500">
                <span className={`font-bold ${fileCount > BATCH_LIMITS.MAX_FILES ? 'text-red-600' : 'text-gray-800'}`}>{fileCount}</span>
                <span>/{BATCH_LIMITS.MAX_FILES} archivos</span>
              </div>
              <div className="text-xs text-gray-500">
                <span className={`font-bold ${totalPages > BATCH_LIMITS.MAX_PAGES_TOTAL ? 'text-red-600' : 'text-gray-800'}`}>
                  {isReadingPages ? '…' : totalPages}
                </span>
                <span>/{BATCH_LIMITS.MAX_PAGES_TOTAL} págs.</span>
              </div>
              <div className="text-xs text-gray-500">
                <span className={`font-bold ${totalSize > BATCH_LIMITS.MAX_TOTAL_SIZE ? 'text-red-600' : 'text-gray-800'}`}>{formatMB(totalSize)}</span>
                <span>/50 MB</span>
              </div>
            </div>
            <button onClick={e => { e.stopPropagation(); clearAll(); }} className="text-xs text-gray-400 hover:text-red-500 transition-colors">
              Limpiar todo
            </button>
          </div>

          {/* Barras de progreso */}
          <div className="px-4 py-2 space-y-1.5 border-b border-gray-100">
            {/* Archivos */}
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-400 w-16">Archivos</span>
              <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div className={`h-1.5 rounded-full transition-all duration-300 ${pctFiles >= 100 ? 'bg-red-400' : 'bg-purple-400'}`} style={{ width: `${pctFiles}%` }} />
              </div>
              <span className="text-xs text-gray-400 w-12 text-right">{fileCount}/{BATCH_LIMITS.MAX_FILES}</span>
            </div>
            {/* Páginas */}
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-400 w-16">Páginas</span>
              <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                {isReadingPages
                  ? <div className="h-1.5 bg-purple-200 rounded-full animate-pulse w-full" />
                  : <div className={`h-1.5 rounded-full transition-all duration-300 ${pctPages >= 100 ? 'bg-red-400' : 'bg-indigo-400'}`} style={{ width: `${pctPages}%` }} />
                }
              </div>
              <span className="text-xs text-gray-400 w-12 text-right">
                {isReadingPages ? <Loader2 size={10} className="animate-spin inline" /> : `${totalPages}/${BATCH_LIMITS.MAX_PAGES_TOTAL}`}
              </span>
            </div>
            {/* Tamaño */}
            <div className="flex items-center space-x-2">
              <span className="text-xs text-gray-400 w-16">Tamaño</span>
              <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div className={`h-1.5 rounded-full transition-all duration-300 ${pctSize >= 100 ? 'bg-red-400' : 'bg-blue-400'}`} style={{ width: `${pctSize}%` }} />
              </div>
              <span className="text-xs text-gray-400 w-12 text-right">{formatMB(totalSize)}</span>
            </div>
          </div>

          {/* Filas de archivos */}
          <ul className="divide-y divide-gray-50 max-h-52 overflow-y-auto">
            {selectedFiles.map((file, idx) => {
              const overSize  = file.size > BATCH_LIMITS.MAX_SIZE_PER_FILE;
              const badType   = !(BATCH_LIMITS.ACCEPTED_TYPES as readonly string[]).includes(file.type);
              const pages     = pageCounts.get(fileKey(file));
              const badPages  = pages !== undefined && pages !== null && pages > BATCH_LIMITS.MAX_PAGES_PER_FILE;
              const corrupt   = pages === null;
              const hasIssue  = overSize || badType || badPages || corrupt;
              const pageLabel = pages === undefined
                ? null
                : pages === null
                ? '?'
                : `${pages}p`;

              return (
                <li
                  key={fileKey(file)}
                  className={`flex items-center space-x-3 px-4 py-2.5 transition-colors ${hasIssue ? 'bg-red-50/40' : 'hover:bg-gray-50'}`}
                >
                  {corrupt
                    ? <FileX size={16} className="text-red-400 flex-shrink-0" />
                    : <FileText size={16} className={hasIssue ? 'text-red-400' : 'text-purple-400'} />
                  }

                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium truncate ${hasIssue ? 'text-red-700' : 'text-gray-800'}`}>
                      {file.name}
                    </p>
                    <p className={`text-xs ${overSize ? 'text-red-500' : 'text-gray-400'}`}>
                      {formatMB(file.size)}{overSize ? ' — supera 10 MB' : ''}
                    </p>
                  </div>

                  {/* Badge de páginas */}
                  <span className={`text-xs font-semibold px-1.5 py-0.5 rounded flex-shrink-0 ${
                    pages === undefined     ? 'text-gray-300'
                    : corrupt               ? 'text-red-500 bg-red-100'
                    : badPages              ? 'text-red-600 bg-red-100'
                    : 'text-indigo-600 bg-indigo-50'
                  }`}>
                    {isReadingPages && pages === undefined
                      ? <Loader2 size={10} className="animate-spin" />
                      : pageLabel
                    }
                  </span>

                  {hasIssue
                    ? <AlertCircle size={15} className="text-red-400 flex-shrink-0" />
                    : <CheckCircle2 size={15} className="text-green-400 flex-shrink-0" />
                  }

                  <button
                    onClick={e => removeFile(idx, e)}
                    className="text-gray-300 hover:text-red-500 transition-colors flex-shrink-0"
                    title="Quitar archivo"
                  >
                    <X size={15} />
                  </button>
                </li>
              );
            })}
          </ul>

          {/* Botón procesar */}
          <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
            <button
              onClick={e => { e.stopPropagation(); handleSubmit(); }}
              disabled={!canSubmit}
              className={`w-full flex items-center justify-center space-x-2 py-2.5 rounded-lg font-semibold text-sm transition-all duration-200
                ${canSubmit
                  ? 'bg-purple-600 text-white hover:bg-purple-700 shadow-sm hover:shadow-md'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }
              `}
            >
              {isLoading ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  <span>Procesando lote con IA...</span>
                </>
              ) : isReadingPages ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  <span>Leyendo páginas...</span>
                </>
              ) : (
                <span>
                  {hasErrors
                    ? 'Corrige los errores para continuar'
                    : `Procesar ${fileCount} documento${fileCount > 1 ? 's' : ''} · ${totalPages} pág.`
                  }
                </span>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
