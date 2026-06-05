import { useState } from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Eye, FileText, BarChart2, Clock, Download, FileSpreadsheet } from 'lucide-react';
import type { BatchFile } from '../types/batch';
import { formatMB } from '../types/batch';
import { exportToExcel, exportToCSV, exportToTXT } from '../services/export.service';

// ─── Detección de campos problemáticos en el lote ─────────────────────────────

/** Cuenta cuántos documentos del lote tienen al menos un campo con confianza BAJA o advertencia SUNAT. */
function contarDocumentosConProblemas(files: BatchFile[]): number {
  return files.filter(f => {
    const d = f.result;
    if (!d) return false;
    const ev = f.editedValues ?? {};
    const campos = [
      { key: 'comprobante.tipo',          field: d.comprobante.tipo },
      { key: 'comprobante.serie',         field: d.comprobante.serie },
      { key: 'comprobante.numero',        field: d.comprobante.numero },
      { key: 'comprobante.fecha_emision', field: d.comprobante.fecha_emision },
      { key: 'comprobante.moneda',        field: d.comprobante.moneda },
      { key: 'emisor.ruc',                field: d.emisor.ruc },
      { key: 'emisor.razon_social',       field: d.emisor.razon_social },
      { key: 'receptor.ruc_dni',          field: d.receptor.ruc_dni },
      { key: 'receptor.razon_social',     field: d.receptor.razon_social },
      { key: 'montos.subtotal',           field: d.montos.subtotal },
      { key: 'montos.igv',                field: d.montos.igv },
      { key: 'montos.total',              field: d.montos.total },
    ];
    const tieneBaja = campos.some(c => !(c.key in ev) && c.field?.confianza === 'BAJA');
    // Verificar número SUNAT: tanto del backend como el valor editado
    const editedNum = ev['comprobante.numero'];
    let tieneSunatAdv = false;
    if (editedNum) {
      const digitos = editedNum.replace(/\D/g, '');
      tieneSunatAdv = digitos.length > 8;
    } else {
      tieneSunatAdv = !!d.comprobante.numero_sunat_advertencia;
    }
    return tieneBaja || tieneSunatAdv;
  }).length;
}

interface ResultsTableProps {
  files: BatchFile[];
  onSelectFile: (index: number) => void;
}

// ─── Badge de estado ──────────────────────────────────────────────────────────

const StatusBadge = ({ status }: { status: BatchFile['status'] }) => {
  const cfg = {
    completado: { label: 'Completado',        icon: <CheckCircle2 size={13} />, cls: 'bg-green-100 text-green-700'  },
    revision:   { label: 'Revisar',           icon: <AlertTriangle size={13} />, cls: 'bg-yellow-100 text-yellow-700' },
    error:      { label: 'Error',             icon: <XCircle size={13} />,       cls: 'bg-red-100 text-red-700'       },
    pendiente:  { label: 'Pendiente',         icon: null,                         cls: 'bg-gray-100 text-gray-500'     },
    procesando: { label: 'Procesando',        icon: null,                         cls: 'bg-purple-100 text-purple-600' },
  }[status];

  return (
    <span className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs font-semibold ${cfg.cls}`}>
      {cfg.icon}
      <span>{cfg.label}</span>
    </span>
  );
};

// ─── Barra de score ───────────────────────────────────────────────────────────

const ScoreBar = ({ score }: { score: number }) => {
  const color =
    score >= 80 ? 'bg-green-400' :
    score >= 55 ? 'bg-yellow-400' :
    'bg-red-400';
  return (
    <div className="flex items-center space-x-2 min-w-[80px]">
      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs font-bold text-gray-700 w-8 text-right">{score}%</span>
    </div>
  );
};

// ─── Componente principal ─────────────────────────────────────────────────────

export default function ResultsTable({ files, onSelectFile }: ResultsTableProps) {
  const done      = files.filter(f => f.status === 'completado' || f.status === 'revision');
  const errCount  = files.filter(f => f.status === 'error').length;
  const avgScore  = done.length > 0
    ? Math.round(done.reduce((acc, f) => acc + (f.result?.metricas?.score_promedio ?? 0), 0) / done.length)
    : 0;
  const totalTime = files.reduce((acc, f) => acc + (f.result?.metricas?.tiempo_procesamiento ?? 0), 0);

  // ── Modal de advertencia para exportación ───────────────────────────────
  const [exportPending, setExportPending] = useState<(() => void) | null>(null);
  const docsCon = contarDocumentosConProblemas(files);

  const handleExport = (fn: () => void) => {
    if (docsCon > 0) {
      setExportPending(() => fn);  // guardar la función a ejecutar
    } else {
      fn();
    }
  };

  return (
    <div className="w-full bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">

      {/* Header del lote */}
      <div className="bg-purple-600 text-white px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText size={20} />
          <h2 className="text-lg font-semibold">Resultados del Lote</h2>
        </div>
        <div className="flex items-center space-x-3">
          {/* Métricas inline */}
          <span className="flex items-center space-x-1 text-purple-200 text-sm">
            <CheckCircle2 size={14} className="text-green-300" />
            <span>{done.length} procesados</span>
          </span>
          {errCount > 0 && (
            <span className="flex items-center space-x-1 text-purple-200 text-sm">
              <XCircle size={14} className="text-red-300" />
              <span>{errCount} errores</span>
            </span>
          )}

          {/* Separador */}
          {done.length > 0 && <span className="text-purple-400">|</span>}

          {/* Botones de exportación — solo si hay resultados */}
          {done.length > 0 && (
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleExport(() => exportToExcel(files))}
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-white text-purple-700 rounded-lg text-xs font-semibold hover:bg-purple-50 transition-colors shadow-sm"
                title="Descargar resultados en Excel"
              >
                <FileSpreadsheet size={14} />
                <span>Excel</span>
              </button>
              <button
                onClick={() => handleExport(() => exportToCSV(files))}
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-purple-500 text-white rounded-lg text-xs font-semibold hover:bg-purple-400 transition-colors border border-purple-400"
                title="Descargar resultados en CSV"
              >
                <Download size={14} />
                <span>CSV</span>
              </button>
              <button
                onClick={() => handleExport(() => exportToTXT(files))}
                className="flex items-center space-x-1.5 px-3 py-1.5 bg-purple-500 text-white rounded-lg text-xs font-semibold hover:bg-purple-400 transition-colors border border-purple-400"
                title="Descargar reporte en texto plano"
              >
                <FileText size={14} />
                <span>TXT</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Resumen estadístico */}
      <div className="grid grid-cols-3 divide-x divide-gray-100 border-b border-gray-100">
        <div className="px-6 py-3 text-center">
          <p className="text-xs text-gray-400 uppercase tracking-wide">Documentos</p>
          <p className="text-xl font-bold text-gray-800 mt-0.5">{files.length}</p>
        </div>
        <div className="px-6 py-3 text-center">
          <p className="text-xs text-gray-400 uppercase tracking-wide flex items-center justify-center space-x-1">
            <BarChart2 size={11} /><span>Precisión media</span>
          </p>
          <p className={`text-xl font-bold mt-0.5 ${avgScore >= 80 ? 'text-green-600' : avgScore >= 55 ? 'text-yellow-600' : 'text-red-600'}`}>
            {avgScore}%
          </p>
        </div>
        <div className="px-6 py-3 text-center">
          <p className="text-xs text-gray-400 uppercase tracking-wide flex items-center justify-center space-x-1">
            <Clock size={11} /><span>Tiempo total</span>
          </p>
          <p className="text-xl font-bold text-gray-800 mt-0.5">{totalTime.toFixed(1)}s</p>
        </div>
      </div>

      {/* Tabla */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-100 text-xs text-gray-400 uppercase tracking-wider">
              <th className="text-left px-4 py-3 font-semibold">#</th>
              <th className="text-left px-4 py-3 font-semibold">Archivo</th>
              <th className="text-left px-4 py-3 font-semibold">Tipo</th>
              <th className="text-left px-4 py-3 font-semibold">RUC Emisor</th>
              <th className="text-right px-4 py-3 font-semibold">Total (S/)</th>
              <th className="text-center px-4 py-3 font-semibold">Precisión</th>
              <th className="text-center px-4 py-3 font-semibold">Estado</th>
              <th className="text-center px-4 py-3 font-semibold">Ver</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {files.map((batchFile, idx) => {
              const d = batchFile.result;
              const tipo  = d?.comprobante?.tipo?.valor  ?? '—';
              const ruc   = d?.emisor?.ruc?.valor        ?? '—';
              const total = d?.montos?.total?.valor;
              const score = d?.metricas?.score_promedio  ?? 0;
              const hasResult = batchFile.status === 'completado' || batchFile.status === 'revision';

              return (
                <tr
                  key={batchFile.id}
                  className={`transition-colors ${hasResult ? 'hover:bg-purple-50/30 cursor-pointer' : 'opacity-60'}`}
                  onClick={() => hasResult && onSelectFile(idx)}
                >
                  {/* Número */}
                  <td className="px-4 py-3 text-gray-400 font-mono text-xs">{idx + 1}</td>

                  {/* Nombre del archivo */}
                  <td className="px-4 py-3">
                    <p className="font-medium text-gray-800 truncate max-w-[180px]" title={batchFile.file.name}>
                      {batchFile.file.name}
                    </p>
                    <p className="text-xs text-gray-400">{formatMB(batchFile.file.size)}</p>
                  </td>

                  {/* Tipo comprobante */}
                  <td className="px-4 py-3 text-gray-600 truncate max-w-[120px]" title={tipo}>
                    {tipo}
                  </td>

                  {/* RUC Emisor */}
                  <td className="px-4 py-3 font-mono text-gray-600 text-xs">{ruc}</td>

                  {/* Total */}
                  <td className="px-4 py-3 text-right font-semibold text-gray-800">
                    {total != null
                      ? Number(total).toLocaleString('es-PE', { minimumFractionDigits: 2 })
                      : batchFile.error
                      ? <span className="text-xs text-red-400 font-normal">{batchFile.error}</span>
                      : '—'
                    }
                  </td>

                  {/* Precisión */}
                  <td className="px-4 py-3">
                    {hasResult ? <ScoreBar score={score} /> : <span className="text-gray-300 text-xs">—</span>}
                  </td>

                  {/* Estado */}
                  <td className="px-4 py-3 text-center">
                    <StatusBadge status={batchFile.status} />
                  </td>

                  {/* Botón Ver */}
                  <td className="px-4 py-3 text-center">
                    {hasResult ? (
                      <button
                        onClick={e => { e.stopPropagation(); onSelectFile(idx); }}
                        className="inline-flex items-center space-x-1 text-purple-500 hover:text-purple-700 transition-colors text-xs font-medium"
                        title="Ver detalles del documento"
                      >
                        <Eye size={15} />
                        <span>Ver</span>
                      </button>
                    ) : (
                      <span className="text-gray-300 text-xs">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* ── Modal de advertencia al exportar ────────────────────────────── */}
      {exportPending !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 p-7 max-w-sm w-full mx-4">
            <div className="text-center mb-5">
              <div className="w-14 h-14 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <AlertTriangle className="text-yellow-500" size={28} />
              </div>
              <h3 className="text-lg font-bold text-gray-900">
                {docsCon} documento{docsCon > 1 ? 's' : ''} con baja precisión
              </h3>
              <p className="text-sm text-gray-500 mt-2">
                {docsCon > 1
                  ? `Hay ${docsCon} documentos con campos de precisión roja o número SUNAT inválido.`
                  : 'Hay 1 documento con campos de precisión roja o número SUNAT inválido.'}
                {' '}¿Desea exportar igualmente?
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setExportPending(null)}
                className="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-700 font-semibold text-sm hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={() => { exportPending(); setExportPending(null); }}
                className="flex-1 py-2.5 rounded-xl bg-purple-600 text-white font-semibold text-sm hover:bg-purple-700 transition-colors"
              >
                Exportar igualmente
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
