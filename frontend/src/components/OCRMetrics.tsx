import type { MetricasOCR } from '../types/invoice';
import { Clock, Target, BarChart2, Layers } from 'lucide-react';

interface OCRMetricsProps {
  metricas: MetricasOCR;
}

interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
  subtext?: string;
  color: string;
}

const MetricCard = ({ icon, label, value, subtext, color }: MetricCardProps) => (
  <div className={`bg-white rounded-xl border ${color} p-4 flex flex-col items-center text-center shadow-sm hover:shadow-md transition-shadow`}>
    <div className={`mb-2 ${color.replace('border-', 'text-')}`}>
      {icon}
    </div>
    <span className="text-2xl font-bold text-gray-900">{value}</span>
    <span className="text-xs font-semibold text-gray-500 mt-1">{label}</span>
    {subtext && (
      <span className="text-xs text-gray-400 mt-0.5">{subtext}</span>
    )}
  </div>
);

export default function OCRMetrics({ metricas }: OCRMetricsProps) {
  const { tiempo_procesamiento, campos_detectados, total_campos, score_promedio } = metricas;

  // Color del score promedio según rango
  const scoreBorderColor =
    score_promedio >= 80 ? 'border-green-300' :
    score_promedio >= 55 ? 'border-yellow-300' :
    'border-red-300';

  const scoreTextColor =
    score_promedio >= 80 ? 'text-green-500' :
    score_promedio >= 55 ? 'text-yellow-500' :
    'text-red-500';

  const camposOk = campos_detectados === total_campos;

  return (
    <div className="w-full">
      <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3 flex items-center space-x-2">
        <BarChart2 size={14} />
        <span>Métricas del Pipeline</span>
      </h3>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {/* Tiempo de procesamiento */}
        <MetricCard
          icon={<Clock size={22} />}
          label="Tiempo"
          value={`${tiempo_procesamiento}s`}
          subtext="procesamiento"
          color="border-blue-200"
        />

        {/* Campos detectados */}
        <MetricCard
          icon={<Layers size={22} />}
          label="Campos"
          value={`${campos_detectados}/${total_campos}`}
          subtext={camposOk ? 'todos detectados' : 'parcial'}
          color={camposOk ? 'border-green-200' : 'border-yellow-200'}
        />

        {/* Score promedio */}
        <MetricCard
          icon={<span className={scoreTextColor}><Target size={22} /></span>}
          label="Precisión"
          value={`${score_promedio}%`}
          subtext="score promedio"
          color={scoreBorderColor}
        />

        {/* Confianza general (derivada) */}
        <MetricCard
          icon={<BarChart2 size={22} />}
          label="Confianza"
          value={score_promedio >= 80 ? 'ALTA' : score_promedio >= 55 ? 'MEDIA' : 'BAJA'}
          subtext="nivel global"
          color={score_promedio >= 80 ? 'border-green-200' : score_promedio >= 55 ? 'border-yellow-200' : 'border-red-200'}
        />
      </div>
    </div>
  );
}
