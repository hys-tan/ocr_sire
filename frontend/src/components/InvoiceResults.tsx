import type { InvoiceResponse, ConfidenceField, ConfianzaNivel } from '../types/invoice';
import { CheckCircle2, AlertTriangle, XCircle, FileText, User, Building, Calculator } from 'lucide-react';

interface InvoiceResultsProps {
  data: InvoiceResponse;
}

const ConfidenceBadge = ({ level, tooltip, score }: { level: ConfianzaNivel, tooltip: string, score: number }) => {
  const pct = `${score}%`;
  if (level === "ALTA") return (
    <span title={tooltip} className="flex items-center space-x-1">
      <CheckCircle2 className="text-green-500" size={16} />
      <span className="text-xs font-bold text-green-600">{pct}</span>
    </span>
  );
  if (level === "MEDIA") return (
    <span title={tooltip} className="flex items-center space-x-1">
      <AlertTriangle className="text-yellow-500" size={16} />
      <span className="text-xs font-bold text-yellow-600">{pct}</span>
    </span>
  );
  return (
    <span title={tooltip} className="flex items-center space-x-1">
      <XCircle className="text-red-500" size={16} />
      <span className="text-xs font-bold text-red-600">{pct}</span>
    </span>
  );
};

const formatValue = (valor: any): string => {
  if (valor === null || valor === undefined) return 'No detectado';
  if (typeof valor === 'number') {
    return valor.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  return String(valor);
};

const FieldRow = ({ label, field }: { label: string, field: ConfidenceField<any> | undefined | null }) => {
  if (!field) return null;
  
  const isBaja = field.confianza === "BAJA";
  const isMedia = field.confianza === "MEDIA";
  
  let bgClass = "bg-white";
  if (isBaja) bgClass = "bg-red-50/50 border-l-4 border-red-500";
  else if (isMedia) bgClass = "bg-yellow-50/50 border-l-4 border-yellow-400";
  else bgClass = "border-l-4 border-green-500";
  
  const displayValue = formatValue(field.valor);
  
  return (
    <div className={`flex justify-between items-center p-3 border-b border-gray-100 last:border-0 ${bgClass}`}>
      <span className="text-sm font-medium text-gray-500 w-1/3 pl-2">{label}</span>
      <div className="flex items-center space-x-3 w-2/3 justify-end text-right">
        <span className={`text-sm font-semibold truncate ${isBaja ? 'text-red-700' : 'text-gray-900'}`} title={displayValue}>
          {displayValue}
        </span>
        <div className="cursor-help flex-shrink-0">
          <ConfidenceBadge level={field.confianza} tooltip={field.estrategia} score={field.score} />
        </div>
      </div>
    </div>
  );
};

// Calcula el score promedio ponderado de todos los campos del documento
function calcularScoreGlobal(data: InvoiceResponse): number {
  const campos = [
    data.comprobante.tipo,
    data.comprobante.serie_numero,
    data.comprobante.fecha_emision,
    data.comprobante.moneda,
    data.emisor.ruc,
    data.emisor.razon_social,
    data.receptor.ruc_dni,
    data.receptor.razon_social,
    data.montos.subtotal,
    data.montos.igv,
    data.montos.total,
  ];
  const validos = campos.filter(Boolean) as ConfidenceField<any>[];
  if (validos.length === 0) return 0;
  const suma = validos.reduce((acc, f) => acc + (f.score ?? 0), 0);
  return Math.round(suma / validos.length);
}

export default function InvoiceResults({ data }: InvoiceResultsProps) {
  const scoreGlobal = calcularScoreGlobal(data);
  const scoreColor =
    scoreGlobal >= 80 ? 'text-green-600' :
    scoreGlobal >= 55 ? 'text-yellow-600' :
    'text-red-600';
  const barColor =
    scoreGlobal >= 80 ? 'bg-green-500' :
    scoreGlobal >= 55 ? 'bg-yellow-400' :
    'bg-red-500';
  const label =
    scoreGlobal >= 80 ? 'Alta precisión' :
    scoreGlobal >= 55 ? 'Precisión media — Revisar campos marcados' :
    'Baja precisión — Revisión manual recomendada';
  return (
    <div className="w-full bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col h-full max-h-[700px]">
      <div className="bg-purple-600 text-white px-6 py-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center space-x-2">
          <FileText size={20} />
          <span>Resultados OCR</span>
        </h2>
        <span className="text-xs bg-purple-500 px-2 py-1 rounded-full font-mono">
          IA V5 Activa
        </span>
      </div>

      <div className="overflow-y-auto flex-1 p-4 space-y-6">
        
        {/* Sección Comprobante */}
        <section>
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center space-x-2">
            <FileText size={14} />
            <span>Datos del Comprobante</span>
          </h3>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            <FieldRow label="Tipo" field={data.comprobante.tipo} />
            <FieldRow label="Serie y Número" field={data.comprobante.serie_numero} />
            <FieldRow label="Fecha Emisión" field={data.comprobante.fecha_emision} />
            <FieldRow label="Moneda" field={data.comprobante.moneda} />
          </div>
        </section>

        {/* Sección Emisor */}
        <section>
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center space-x-2">
            <Building size={14} />
            <span>Datos del Emisor</span>
          </h3>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            <FieldRow label="RUC" field={data.emisor.ruc} />
            <FieldRow label="Razón Social" field={data.emisor.razon_social} />
          </div>
        </section>

        {/* Sección Receptor */}
        <section>
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center space-x-2">
            <User size={14} />
            <span>Datos del Receptor</span>
          </h3>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            <FieldRow label="RUC / DNI" field={data.receptor.ruc_dni} />
            <FieldRow label="Razón Social" field={data.receptor.razon_social} />
          </div>
        </section>

        {/* Sección Montos */}
        <section>
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center space-x-2">
            <Calculator size={14} />
            <span>Montos y Totales</span>
          </h3>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            <FieldRow label="Subtotal" field={data.montos.subtotal} />
            <FieldRow label="IGV (18%)" field={data.montos.igv} />
            <FieldRow label="Total" field={data.montos.total} />
          </div>
        </section>

      </div>
      
      {/* Footer: Métrica global */}
      <div className="bg-gray-50 border-t border-gray-200 px-5 py-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Precisión Global OCR</span>
          <span className={`text-sm font-bold ${scoreColor}`}>{scoreGlobal}%</span>
        </div>
        {/* Barra de progreso */}
        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
          <div
            className={`h-2 rounded-full transition-all duration-700 ${barColor}`}
            style={{ width: `${scoreGlobal}%` }}
          />
        </div>
        <p className={`text-xs mt-2 ${scoreColor} font-medium`}>{label}</p>
      </div>
    </div>
  );
}
