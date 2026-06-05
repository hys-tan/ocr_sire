import { useState } from 'react';
import { ChevronLeft, ChevronRight, ArrowLeft, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import PDFViewer from './PDFViewer';
import InvoiceResults from './InvoiceResults';
import OCRMetrics from './OCRMetrics';
import type { BatchFile } from '../types/batch';
import type { InvoiceResponse } from '../types/invoice';

interface InvoiceViewerProps {
  files: BatchFile[];
  activeIndex: number;
  onBack: () => void;
  onNavigate: (index: number) => void;
  onFileEdit: (id: string, edits: Record<string, string>) => void;
}

// ─── Detección de campos problemáticos ───────────────────────────────────────

/**
 * Devuelve la lista de etiquetas de campos con confianza BAJA o con
 * advertencia en el número SUNAT (más de 8 dígitos).
 * Excluye los que el usuario ya corrigió manualmente.
 */
function detectarProblemas(result: InvoiceResponse, editedValues: Record<string, string>): string[] {
  const CAMPOS: { label: string; key: string; field: any }[] = [
    { label: 'Tipo Comprobante',     key: 'comprobante.tipo',          field: result.comprobante.tipo },
    { label: 'Serie',                key: 'comprobante.serie',         field: result.comprobante.serie },
    { label: 'Número',               key: 'comprobante.numero',        field: result.comprobante.numero },
    { label: 'Fecha Emisión',        key: 'comprobante.fecha_emision', field: result.comprobante.fecha_emision },
    { label: 'Moneda',               key: 'comprobante.moneda',        field: result.comprobante.moneda },
    { label: 'RUC Emisor',           key: 'emisor.ruc',                field: result.emisor.ruc },
    { label: 'Razón Social Emisor',  key: 'emisor.razon_social',       field: result.emisor.razon_social },
    { label: 'RUC / DNI Receptor',   key: 'receptor.ruc_dni',          field: result.receptor.ruc_dni },
    { label: 'Razón Social Receptor',key: 'receptor.razon_social',     field: result.receptor.razon_social },
    { label: 'Subtotal',             key: 'montos.subtotal',           field: result.montos.subtotal },
    { label: 'IGV',                  key: 'montos.igv',                field: result.montos.igv },
    { label: 'Total',                key: 'montos.total',              field: result.montos.total },
  ];

  const problemas: string[] = [];

  for (const c of CAMPOS) {
    // Si el usuario ya corrigió este campo, no contar como problema
    if (c.key in editedValues) continue;
    if (c.field?.confianza === 'BAJA') problemas.push(c.label);
  }

  // Número SUNAT: verificar tanto el valor del backend como el editado manualmente
  const editedNumero = editedValues['comprobante.numero'];
  if (editedNumero) {
    // El usuario editó el número: reevaluar con la misma regla de padding
    const soloDigitos = editedNumero.replace(/\D/g, '');
    if (soloDigitos.length > 8) {
      problemas.push(`Número SUNAT (${soloDigitos.length} dígitos, máximo 8)`);
    }
  } else if (result.comprobante.numero_sunat_advertencia) {
    // No fue editado y el backend detectó anomalía
    problemas.push('Número SUNAT (formato inválido)');
  }

  return problemas;
}

// ─── Badge de estado inline ───────────────────────────────────────────────────

const StatusChip = ({ status }: { status: BatchFile['status'] }) => {
  const cfg = {
    completado: { icon: <CheckCircle2 size={13} />, label: 'Completado',  cls: 'text-green-600 bg-green-50 border-green-200' },
    revision:   { icon: <AlertTriangle size={13} />, label: 'Revisar',    cls: 'text-yellow-600 bg-yellow-50 border-yellow-200' },
    error:      { icon: <XCircle size={13} />,       label: 'Error',      cls: 'text-red-600 bg-red-50 border-red-200' },
    pendiente:  { icon: null,                         label: 'Pendiente',  cls: 'text-gray-500 bg-gray-50 border-gray-200' },
    procesando: { icon: null,                         label: 'Procesando', cls: 'text-purple-600 bg-purple-50 border-purple-200' },
  }[status];

  return (
    <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold border ${cfg.cls}`}>
      {cfg.icon}
      <span>{cfg.label}</span>
    </span>
  );
};

// ─── Componente principal ─────────────────────────────────────────────────────

export default function InvoiceViewer({ files, activeIndex, onBack, onNavigate, onFileEdit }: InvoiceViewerProps) {
  const activeFile   = files[activeIndex];
  const activeResult = activeFile?.result ?? null;
  const editedValues = activeFile?.editedValues ?? {};

  const hasPrev = activeIndex > 0;
  const hasNext = activeIndex < files.length - 1;

  // ── Modal de advertencia ──────────────────────────────────────────────────
  const [showWarn, setShowWarn] = useState(false);
  const [warnProblemas, setWarnProblemas] = useState<string[]>([]);

  const handleBackClick = () => {
    if (!activeResult) { onBack(); return; }
    const problemas = detectarProblemas(activeResult, editedValues);
    if (problemas.length > 0) {
      setWarnProblemas(problemas);
      setShowWarn(true);
    } else {
      onBack();
    }
  };

  // Contar cuántos tienen resultado para mostrar en la navegación
  const hasResultAt = (idx: number) =>
    files[idx]?.status === 'completado' || files[idx]?.status === 'revision';

  if (!activeFile) return null;

  return (
    <div className="flex flex-col gap-4 mt-2">

      {/* ── Barra de navegación superior ──────────────────────────────────── */}
      <div className="flex items-center justify-between bg-white rounded-xl border border-gray-200 shadow-sm px-4 py-3">

        {/* Volver — botón prominente con contexto */}
        <button
          onClick={handleBackClick}
          className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-xl font-semibold text-sm hover:bg-purple-700 transition-colors shadow-sm group"
        >
          <ArrowLeft size={16} className="group-hover:-translate-x-0.5 transition-transform" />
          <div className="flex flex-col items-start leading-none">
            <span>Volver al lote</span>
            <span className="text-purple-200 text-xs font-normal mt-0.5">Exportar Excel / CSV / TXT</span>
          </div>
        </button>

        {/* Info del documento activo */}
        <div className="flex flex-col items-center">
          <p className="text-sm font-semibold text-gray-800 max-w-xs truncate" title={activeFile.file.name}>
            {activeFile.file.name}
          </p>
          <div className="flex items-center space-x-2 mt-0.5">
            <span className="text-xs text-gray-400">
              {activeIndex + 1} / {files.length}
            </span>
            <StatusChip status={activeFile.status} />
          </div>
        </div>

        {/* Navegación prev / next */}
        <div className="flex items-center space-x-1">
          <button
            onClick={() => hasPrev && onNavigate(activeIndex - 1)}
            disabled={!hasPrev}
            className={`p-2 rounded-lg border transition-all ${
              hasPrev
                ? 'border-gray-200 text-gray-600 hover:bg-purple-50 hover:border-purple-300 hover:text-purple-600'
                : 'border-gray-100 text-gray-300 cursor-not-allowed'
            }`}
            title="Documento anterior"
          >
            <ChevronLeft size={18} />
          </button>

          {/* Puntos indicadores */}
          <div className="hidden sm:flex items-center space-x-1 px-2">
            {files.map((f, idx) => (
              <button
                key={f.id}
                onClick={() => onNavigate(idx)}
                title={f.file.name}
                className={`rounded-full transition-all duration-200 ${
                  idx === activeIndex
                    ? 'w-4 h-2 bg-purple-500'
                    : hasResultAt(idx)
                    ? 'w-2 h-2 bg-gray-300 hover:bg-purple-300'
                    : 'w-2 h-2 bg-red-200 hover:bg-red-300'
                }`}
              />
            ))}
          </div>

          <button
            onClick={() => hasNext && onNavigate(activeIndex + 1)}
            disabled={!hasNext}
            className={`p-2 rounded-lg border transition-all ${
              hasNext
                ? 'border-gray-200 text-gray-600 hover:bg-purple-50 hover:border-purple-300 hover:text-purple-600'
                : 'border-gray-100 text-gray-300 cursor-not-allowed'
            }`}
            title="Documento siguiente"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      {/* ── Layout dual: PDF | OCR ─────────────────────────────────────────── */}
      {activeResult ? (
        <div className="flex flex-col lg:flex-row gap-6 items-start">
          {/* Izquierda: Visor PDF */}
          <div className="w-full lg:w-1/2 sticky top-6">
            <PDFViewer file={activeFile.file} />
          </div>

          {/* Derecha: Datos OCR + Métricas */}
          <div className="w-full lg:w-1/2 flex flex-col gap-4">
            <InvoiceResults
              data={activeResult}
              editedValues={editedValues}
              onEditChange={(edits) => onFileEdit(activeFile.id, edits)}
            />
            <OCRMetrics metricas={activeResult.metricas} />
          </div>
        </div>
      ) : (
        /* Estado error — sin resultado OCR */
        <div className="bg-red-50 border border-red-200 rounded-xl p-8 text-center">
          <XCircle className="text-red-400 mx-auto mb-3" size={40} />
          <p className="text-red-700 font-semibold">No hay datos OCR para este documento</p>
          <p className="text-red-500 text-sm mt-1">{activeFile.error ?? 'El archivo no pudo procesarse correctamente.'}</p>
          <div className="flex justify-center space-x-3 mt-5">
            {hasPrev && (
              <button
                onClick={() => onNavigate(activeIndex - 1)}
                className="flex items-center space-x-1 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors"
              >
                <ChevronLeft size={15} /> <span>Anterior</span>
              </button>
            )}
            {hasNext && (
              <button
                onClick={() => onNavigate(activeIndex + 1)}
                className="flex items-center space-x-1 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors"
              >
                <span>Siguiente</span> <ChevronRight size={15} />
              </button>
            )}
          </div>
        </div>
      )}

      {/* ── Modal de advertencia: campos con baja precisión ───────────────── */}
      {showWarn && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 p-7 max-w-md w-full mx-4">
            <div className="text-center mb-4">
              <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <XCircle className="text-red-500" size={28} />
              </div>
              <h3 className="text-lg font-bold text-gray-900">
                {warnProblemas.length} campo{warnProblemas.length > 1 ? 's' : ''} con baja precisión
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                Los siguientes campos tienen precisión roja o un formato inválido:
              </p>
            </div>

            {/* Lista de campos problemáticos */}
            <ul className="mb-5 space-y-1.5 max-h-40 overflow-y-auto">
              {warnProblemas.map((p) => (
                <li key={p} className="flex items-center space-x-2 text-sm text-red-700 bg-red-50 px-3 py-1.5 rounded-lg">
                  <XCircle size={13} className="flex-shrink-0" />
                  <span>{p}</span>
                </li>
              ))}
            </ul>

            <p className="text-xs text-gray-400 text-center mb-5">
              ¿Desea volver al lote igualmente? Podrá exportar los datos, pero se recomienda corregir los campos marcados primero.
            </p>

            <div className="flex gap-3">
              <button
                onClick={() => setShowWarn(false)}
                className="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-700 font-semibold text-sm hover:bg-gray-50 transition-colors"
              >
                Revisar campos
              </button>
              <button
                onClick={() => { setShowWarn(false); onBack(); }}
                className="flex-1 py-2.5 rounded-xl bg-purple-600 text-white font-semibold text-sm hover:bg-purple-700 transition-colors"
              >
                Volver igualmente
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
