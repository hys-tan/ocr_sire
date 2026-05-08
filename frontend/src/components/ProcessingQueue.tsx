import { CheckCircle2, AlertTriangle, XCircle, Loader2, Clock, FileText } from 'lucide-react';
import type { BatchFile, BatchStatus } from '../types/batch';
import { formatMB } from '../types/batch';

interface ProcessingQueueProps {
  files: BatchFile[];
  isVisible: boolean;
}

// ─── Configuración visual por estado ──────────────────────────────────────────

const STATUS_CONFIG: Record<BatchStatus, {
  icon: React.ReactNode;
  label: string;
  rowClass: string;
  barClass: string;
  barWidth: string;
}> = {
  pendiente: {
    icon: <Clock size={18} className="text-gray-400" />,
    label: 'Pendiente',
    rowClass: 'opacity-50',
    barClass: 'bg-gray-200',
    barWidth: '0%',
  },
  procesando: {
    icon: <Loader2 size={18} className="text-purple-500 animate-spin" />,
    label: 'Procesando...',
    rowClass: 'bg-purple-50/60',
    barClass: 'bg-purple-400',
    barWidth: '60%',
  },
  completado: {
    icon: <CheckCircle2 size={18} className="text-green-500" />,
    label: 'Completado',
    rowClass: '',
    barClass: 'bg-green-400',
    barWidth: '100%',
  },
  revision: {
    icon: <AlertTriangle size={18} className="text-yellow-500" />,
    label: 'Requiere revisión',
    rowClass: 'bg-yellow-50/40',
    barClass: 'bg-yellow-400',
    barWidth: '100%',
  },
  error: {
    icon: <XCircle size={18} className="text-red-500" />,
    label: 'Error',
    rowClass: 'bg-red-50/40',
    barClass: 'bg-red-400',
    barWidth: '100%',
  },
};

// ─── Componente ───────────────────────────────────────────────────────────────

export default function ProcessingQueue({ files, isVisible }: ProcessingQueueProps) {
  if (!isVisible || files.length === 0) return null;

  const total     = files.length;
  const done      = files.filter(f => f.status !== 'pendiente' && f.status !== 'procesando').length;
  const pctGlobal = Math.round((done / total) * 100);
  const current   = files.find(f => f.status === 'procesando');

  return (
    <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">

        {/* Header */}
        <div className="bg-purple-600 px-6 py-5">
          <div className="flex items-center space-x-3 mb-3">
            <div className="relative">
              <div className="absolute inset-0 bg-purple-300 rounded-full animate-ping opacity-40" />
              <div className="relative bg-purple-100 text-purple-600 p-2.5 rounded-full">
                <Loader2 className="animate-spin" size={22} />
              </div>
            </div>
            <div>
              <h3 className="text-white font-semibold text-base">Procesando lote documental</h3>
              <p className="text-purple-200 text-xs mt-0.5">
                {current
                  ? `Analizando: ${current.file.name}`
                  : 'Preparando documentos...'}
              </p>
            </div>
          </div>

          {/* Barra de progreso global */}
          <div className="space-y-1">
            <div className="flex justify-between text-xs text-purple-200">
              <span>{done}/{total} documentos</span>
              <span>{pctGlobal}%</span>
            </div>
            <div className="w-full bg-purple-800/50 rounded-full h-2 overflow-hidden">
              <div
                className="h-2 bg-white rounded-full transition-all duration-700"
                style={{ width: `${pctGlobal}%` }}
              />
            </div>
          </div>
        </div>

        {/* Lista de archivos */}
        <div className="px-4 py-3 max-h-72 overflow-y-auto space-y-1">
          {files.map((batchFile, idx) => {
            const cfg = STATUS_CONFIG[batchFile.status];
            return (
              <div
                key={batchFile.id}
                className={`flex items-start space-x-3 p-3 rounded-xl transition-all duration-300 ${cfg.rowClass}`}
              >
                {/* Número */}
                <span className="text-xs text-gray-400 w-4 mt-0.5 flex-shrink-0 font-mono">
                  {idx + 1}
                </span>

                {/* Ícono de estado */}
                <div className="flex-shrink-0 mt-0.5">{cfg.icon}</div>

                {/* Info del archivo */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-gray-800 truncate pr-2">
                      {batchFile.file.name}
                    </p>
                    <span className={`text-xs font-semibold flex-shrink-0 ${
                      batchFile.status === 'completado' ? 'text-green-600' :
                      batchFile.status === 'revision'   ? 'text-yellow-600' :
                      batchFile.status === 'error'      ? 'text-red-600' :
                      batchFile.status === 'procesando' ? 'text-purple-600' :
                      'text-gray-400'
                    }`}>
                      {cfg.label}
                    </span>
                  </div>

                  {/* Tamaño + score si está completo */}
                  <p className="text-xs text-gray-400 mt-0.5">
                    {formatMB(batchFile.file.size)}
                    {batchFile.result && (
                      <span className="ml-2 font-medium text-gray-600">
                        · Precisión: {batchFile.result.metricas?.score_promedio ?? '—'}%
                      </span>
                    )}
                    {batchFile.error && (
                      <span className="ml-1 text-red-500">· {batchFile.error}</span>
                    )}
                  </p>

                  {/* Mini barra de progreso por archivo */}
                  <div className="mt-1.5 h-1 w-full bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-1 rounded-full transition-all duration-700 ${cfg.barClass} ${
                        batchFile.status === 'procesando' ? 'animate-pulse' : ''
                      }`}
                      style={{ width: cfg.barWidth }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer informativo */}
        <div className="px-6 py-3 bg-gray-50 border-t border-gray-100">
          <p className="text-xs text-gray-400 text-center flex items-center justify-center space-x-1">
            <FileText size={12} />
            <span>Procesamiento secuencial · Los errores individuales no detienen el lote</span>
          </p>
        </div>

      </div>
    </div>
  );
}
