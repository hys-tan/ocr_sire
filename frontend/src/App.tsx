import { useReducer, useCallback } from 'react';
import UploadSection from './components/UploadSection';
import ProcessingQueue from './components/ProcessingQueue';
import ResultsTable from './components/ResultsTable';
import InvoiceViewer from './components/InvoiceViewer';
import ErrorAlert from './components/ErrorAlert';
import { extractInvoiceData } from './services/api';
import type { InvoiceResponse } from './types/invoice';
import type { BatchFile } from './types/batch';

// ─── Estado del lote ──────────────────────────────────────────────────────────

interface BatchState {
  files: BatchFile[];
  activeIndex: number | null;   // índice del documento visible en la vista dual
  isProcessing: boolean;
  globalError: string | null;
}

const INITIAL_STATE: BatchState = {
  files: [],
  activeIndex: null,
  isProcessing: false,
  globalError: null,
};

// ─── Acciones ─────────────────────────────────────────────────────────────────

type BatchAction =
  | { type: 'ADD_FILES';   files: BatchFile[] }
  | { type: 'SET_STATUS';  id: string; status: BatchFile['status'] }
  | { type: 'SET_RESULT';  id: string; result: InvoiceResponse }
  | { type: 'SET_ERROR';   id: string; error: string }
  | { type: 'UPDATE_FILE_EDITS'; id: string; edits: Record<string, string> }
  | { type: 'SET_ACTIVE';  index: number | null }
  | { type: 'START_PROCESSING' }
  | { type: 'STOP_PROCESSING' }
  | { type: 'SET_GLOBAL_ERROR'; error: string | null }
  | { type: 'RESET' };

function batchReducer(state: BatchState, action: BatchAction): BatchState {
  switch (action.type) {
    case 'ADD_FILES':
      return { ...state, files: action.files, activeIndex: null, globalError: null };

    case 'SET_STATUS':
      return {
        ...state,
        files: state.files.map(f =>
          f.id === action.id ? { ...f, status: action.status } : f
        ),
      };

    case 'SET_RESULT': {
      const score = action.result.metricas?.score_promedio ?? 0;
      const status: BatchFile['status'] = score < 55 ? 'revision' : 'completado';
      return {
        ...state,
        files: state.files.map(f =>
          f.id === action.id ? { ...f, status, result: action.result } : f
        ),
      };
    }

    case 'SET_ERROR':
      return {
        ...state,
        files: state.files.map(f =>
          f.id === action.id ? { ...f, status: 'error', error: action.error } : f
        ),
      };

    case 'UPDATE_FILE_EDITS':
      return {
        ...state,
        files: state.files.map(f =>
          f.id === action.id ? { ...f, editedValues: action.edits } : f
        ),
      };

    case 'SET_ACTIVE':
      return { ...state, activeIndex: action.index };

    case 'START_PROCESSING':
      return { ...state, isProcessing: true, globalError: null };

    case 'STOP_PROCESSING':
      return { ...state, isProcessing: false };

    case 'SET_GLOBAL_ERROR':
      return { ...state, globalError: action.error };

    case 'RESET':
      return INITIAL_STATE;

    default:
      return state;
  }
}

// ─── Componente principal ─────────────────────────────────────────────────────

export default function App() {
  const [state, dispatch] = useReducer(batchReducer, INITIAL_STATE);
  const { files, activeIndex, isProcessing, globalError } = state;

  // Confirmación antes de resetear el lote
  const [showResetConfirm, setShowResetConfirm] = useReducer(
    (_: boolean, next: boolean) => next, false
  );

  // Archivo y resultado activos para la vista dual
  const activeFile   = activeIndex !== null ? files[activeIndex] ?? null : null;
  const activeResult = activeFile?.result ?? null;

  // ¿Hay al menos un resultado para mostrar la tabla/vista?
  const hasResults = files.some(f => f.status === 'completado' || f.status === 'revision' || f.status === 'error');

  // ─── Procesamiento secuencial del lote ──────────────────────────────────────

  const processBatch = useCallback(async (incoming: File[]) => {
    if (incoming.length === 0) return;

    // Crear BatchFile[] para cada archivo
    const batchFiles: BatchFile[] = incoming.map(file => ({
      id: crypto.randomUUID(),
      file,
      status: 'pendiente' as const,
    }));

    dispatch({ type: 'ADD_FILES', files: batchFiles });
    dispatch({ type: 'START_PROCESSING' });

    // Procesar uno a uno (secuencial) — usa el id capturado en el closure
    for (const batchFile of batchFiles) {
      dispatch({ type: 'SET_STATUS', id: batchFile.id, status: 'procesando' });
      try {
        const result = await extractInvoiceData(batchFile.file);
        dispatch({ type: 'SET_RESULT', id: batchFile.id, result });
      } catch (err: any) {
        const msg = err?.message ?? 'Error desconocido al procesar el archivo.';
        dispatch({ type: 'SET_ERROR', id: batchFile.id, error: msg });
      }
    }

    dispatch({ type: 'STOP_PROCESSING' });

    // Auto-activar el primer documento completado
    dispatch({ type: 'SET_ACTIVE', index: 0 });
  }, []);

  const handleReset = () => dispatch({ type: 'RESET' });
  const requestReset = () => setShowResetConfirm(true);
  const confirmReset = () => { setShowResetConfirm(false); dispatch({ type: 'RESET' }); };
  const cancelReset  = () => setShowResetConfirm(false);

  // ─── Vista ──────────────────────────────────────────────────────────────────

  const showUpload  = !isProcessing && !hasResults;
  const showTable   = !isProcessing && hasResults && activeIndex === null;
  const showViewer  = !isProcessing && hasResults && activeResult != null && activeFile != null;

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className={(showViewer || showTable) ? 'max-w-7xl mx-auto' : 'max-w-4xl mx-auto mt-12'}>

        {/* Cabecera */}
        <div className="text-center mb-8 relative">
          <h1 className="text-4xl font-bold text-gray-900 tracking-tight">OCR SIRE</h1>
          <p className="mt-2 text-gray-500">Sistema Inteligente de Extracción de Datos</p>

          {hasResults && (
            <button
              onClick={requestReset}
              className="absolute right-0 top-2 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg text-sm font-medium transition-colors"
            >
              Procesar nuevo lote
            </button>
          )}
        </div>

        <ErrorAlert error={globalError} onClose={() => dispatch({ type: 'SET_GLOBAL_ERROR', error: null })} />

        {/* Vista: Upload */}
        {showUpload && (
          <UploadSection
            onFilesSelect={processBatch}
            isLoading={isProcessing}
          />
        )}

        {/* Vista: Tabla resumen del lote */}
        {showTable && (
          <ResultsTable
            files={files}
            onSelectFile={idx => dispatch({ type: 'SET_ACTIVE', index: idx })}
          />
        )}

        {/* Vista: Documento individual — InvoiceViewer con navegación */}
        {showViewer && activeIndex !== null && (
          <InvoiceViewer
            files={files}
            activeIndex={activeIndex}
            onBack={() => dispatch({ type: 'SET_ACTIVE', index: null })}
            onNavigate={idx => dispatch({ type: 'SET_ACTIVE', index: idx })}
            onFileEdit={(id, edits) => dispatch({ type: 'UPDATE_FILE_EDITS', id, edits })}
          />
        )}

      </div>

      {/* Cola visual de procesamiento */}
      <ProcessingQueue files={files} isVisible={isProcessing} />

      {/* ── Modal de confirmación de reset ──────────────────────────────────── */}
      {showResetConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-100 p-7 max-w-sm w-full mx-4 animate-in">
            <div className="text-center">
              <div className="w-14 h-14 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⚠️</span>
              </div>
              <h3 className="text-lg font-bold text-gray-900">¿Procesar un nuevo lote?</h3>
              <p className="text-sm text-gray-500 mt-2 leading-relaxed">
                Se perderán los resultados actuales del lote
                ({files.filter(f => f.status === 'completado' || f.status === 'revision').length} documentos procesados).
                <br/>
                <span className="font-medium text-gray-700">Asegúrate de haber exportado los datos antes de continuar.</span>
              </p>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={cancelReset}
                className="flex-1 py-2.5 rounded-xl border border-gray-200 text-gray-700 font-semibold text-sm hover:bg-gray-50 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={confirmReset}
                className="flex-1 py-2.5 rounded-xl bg-red-500 text-white font-semibold text-sm hover:bg-red-600 transition-colors"
              >
                Sí, descartar lote
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
