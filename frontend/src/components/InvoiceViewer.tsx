import { ChevronLeft, ChevronRight, ArrowLeft, CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import PDFViewer from './PDFViewer';
import InvoiceResults from './InvoiceResults';
import OCRMetrics from './OCRMetrics';
import type { BatchFile } from '../types/batch';

interface InvoiceViewerProps {
  files: BatchFile[];
  activeIndex: number;
  onBack: () => void;
  onNavigate: (index: number) => void;
}

// ─── Badge de estado inline ───────────────────────────────────────────────────

const StatusChip = ({ status }: { status: BatchFile['status'] }) => {
  const cfg = {
    completado: { icon: <CheckCircle2 size={13} />, label: 'Completado',       cls: 'text-green-600 bg-green-50 border-green-200' },
    revision:   { icon: <AlertTriangle size={13} />, label: 'Revisar',         cls: 'text-yellow-600 bg-yellow-50 border-yellow-200' },
    error:      { icon: <XCircle size={13} />,       label: 'Error',           cls: 'text-red-600 bg-red-50 border-red-200' },
    pendiente:  { icon: null,                         label: 'Pendiente',       cls: 'text-gray-500 bg-gray-50 border-gray-200' },
    procesando: { icon: null,                         label: 'Procesando',      cls: 'text-purple-600 bg-purple-50 border-purple-200' },
  }[status];

  return (
    <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold border ${cfg.cls}`}>
      {cfg.icon}
      <span>{cfg.label}</span>
    </span>
  );
};

// ─── Componente principal ─────────────────────────────────────────────────────

export default function InvoiceViewer({ files, activeIndex, onBack, onNavigate }: InvoiceViewerProps) {
  const activeFile   = files[activeIndex];
  const activeResult = activeFile?.result ?? null;

  const hasPrev = activeIndex > 0;
  const hasNext = activeIndex < files.length - 1;

  // Contar cuántos tienen resultado para mostrar en la navegación
  const hasResultAt = (idx: number) =>
    files[idx]?.status === 'completado' || files[idx]?.status === 'revision';

  if (!activeFile) return null;

  return (
    <div className="flex flex-col gap-4 mt-2">

      {/* ── Barra de navegación superior ──────────────────────────────────── */}
      <div className="flex items-center justify-between bg-white rounded-xl border border-gray-200 shadow-sm px-4 py-3">

        {/* Volver */}
        <button
          onClick={onBack}
          className="flex items-center space-x-1.5 text-sm text-purple-600 hover:text-purple-800 font-medium transition-colors group"
        >
          <ArrowLeft size={16} className="group-hover:-translate-x-0.5 transition-transform" />
          <span>Volver al lote</span>
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
            <InvoiceResults data={activeResult} />
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
    </div>
  );
}
