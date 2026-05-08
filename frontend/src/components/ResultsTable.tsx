import { CheckCircle2, AlertTriangle, XCircle, Eye, FileText, BarChart2, Clock } from 'lucide-react';
import type { BatchFile } from '../types/batch';
import { formatMB } from '../types/batch';

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

  return (
    <div className="w-full bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">

      {/* Header del lote */}
      <div className="bg-purple-600 text-white px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText size={20} />
          <h2 className="text-lg font-semibold">Resultados del Lote</h2>
        </div>
        <div className="flex items-center space-x-4 text-sm">
          <span className="flex items-center space-x-1 text-purple-200">
            <CheckCircle2 size={14} className="text-green-300" />
            <span>{done.length} procesados</span>
          </span>
          {errCount > 0 && (
            <span className="flex items-center space-x-1 text-purple-200">
              <XCircle size={14} className="text-red-300" />
              <span>{errCount} errores</span>
            </span>
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
    </div>
  );
}
