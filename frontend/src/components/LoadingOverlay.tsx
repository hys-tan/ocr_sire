import { useEffect, useState } from 'react';
import { CheckCircle2, Circle, Loader2 } from 'lucide-react';

interface LoadingOverlayProps {
  isVisible: boolean;
  message?: string;
}

const PIPELINE_STEPS = [
  { id: 1, label: 'Documento cargado',      delay: 0    },
  { id: 2, label: 'OCR ejecutado',           delay: 1000 },
  { id: 3, label: 'Extracción completada',   delay: 2200 },
  { id: 4, label: 'Validación finalizada',   delay: 3400 },
];

export default function LoadingOverlay({ isVisible, message = 'Procesando documento con IA...' }: LoadingOverlayProps) {
  const [visibleSteps, setVisibleSteps] = useState<number[]>([]);

  // Cada vez que se activa el overlay, reinicia y programa las animaciones
  useEffect(() => {
    if (!isVisible) {
      setVisibleSteps([]);
      return;
    }

    const timers = PIPELINE_STEPS.map(step =>
      setTimeout(() => {
        setVisibleSteps(prev => [...prev, step.id]);
      }, step.delay)
    );

    return () => timers.forEach(clearTimeout);
  }, [isVisible]);

  if (!isVisible) return null;

  const allDone = visibleSteps.length === PIPELINE_STEPS.length;

  return (
    <div className="fixed inset-0 bg-gray-900/60 backdrop-blur-sm z-50 flex items-center justify-center">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-sm mx-4 overflow-hidden">

        {/* Header animado */}
        <div className="bg-purple-600 px-6 py-5 flex flex-col items-center">
          <div className="relative mb-3">
            <div className="absolute inset-0 bg-purple-300 rounded-full animate-ping opacity-50" />
            <div className="relative bg-purple-100 text-purple-600 p-3 rounded-full">
              <Loader2 className="animate-spin" size={32} />
            </div>
          </div>
          <h3 className="text-white font-semibold text-base">Analizando Documento</h3>
          <p className="text-purple-200 text-xs mt-1">{message}</p>
        </div>

        {/* Pasos del Pipeline */}
        <div className="px-6 py-5 space-y-3">
          <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-4">
            Pipeline de IA
          </p>

          {PIPELINE_STEPS.map(step => {
            const done   = visibleSteps.includes(step.id);
            const active = visibleSteps.length + 1 === step.id; // paso siguiente pendiente

            return (
              <div
                key={step.id}
                className={`flex items-center space-x-3 transition-all duration-500 ${
                  done ? 'opacity-100 translate-x-0' : 'opacity-30'
                }`}
              >
                {/* Icono */}
                <div className="flex-shrink-0">
                  {done ? (
                    <CheckCircle2 className="text-green-500" size={20} />
                  ) : active ? (
                    <Loader2 className="text-purple-400 animate-spin" size={20} />
                  ) : (
                    <Circle className="text-gray-300" size={20} />
                  )}
                </div>

                {/* Línea de progreso + etiqueta */}
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className={`text-sm font-medium ${done ? 'text-gray-800' : 'text-gray-400'}`}>
                      {step.label}
                    </span>
                    {done && (
                      <span className="text-xs text-green-500 font-semibold">✓</span>
                    )}
                  </div>

                  {/* Mini barra de progreso por paso */}
                  <div className="mt-1 h-1 w-full bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-1 rounded-full transition-all duration-700 ${
                        done ? 'bg-green-400 w-full' : 'bg-gray-200 w-0'
                      }`}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer: mensaje final cuando todo está completo */}
        <div
          className={`px-6 py-3 bg-green-50 border-t border-green-100 transition-all duration-500 ${
            allDone ? 'opacity-100 max-h-10' : 'opacity-0 max-h-0 py-0 overflow-hidden'
          }`}
        >
          <p className="text-xs text-green-700 font-semibold text-center">
            ¡Análisis completado! Cargando resultados...
          </p>
        </div>

      </div>
    </div>
  );
}
