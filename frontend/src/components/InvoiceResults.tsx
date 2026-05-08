import { useState, useRef, useEffect } from 'react';
import type { InvoiceResponse, ConfidenceField, ConfianzaNivel } from '../types/invoice';
import { CheckCircle2, AlertTriangle, XCircle, FileText, User, Building, Calculator, Pencil, Check, X } from 'lucide-react';

interface InvoiceResultsProps {
  data: InvoiceResponse;
}

// ─── Badge de Confianza ───────────────────────────────────────────────────────

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

// ─── Badge de corrección manual ───────────────────────────────────────────────

const ManualBadge = () => (
  <span
    title="Valor corregido manualmente por el usuario"
    className="flex items-center space-x-1"
  >
    <CheckCircle2 className="text-purple-500" size={16} />
    <span className="text-xs font-bold text-purple-600">Manual</span>
  </span>
);

// ─── Formato de valores ───────────────────────────────────────────────────────

const formatValue = (valor: any): string => {
  if (valor === null || valor === undefined) return 'No detectado';
  if (typeof valor === 'number') {
    return valor.toLocaleString('es-PE', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  return String(valor);
};

// ─── Fila Editable ────────────────────────────────────────────────────────────

interface EditableFieldRowProps {
  label: string;
  field: ConfidenceField<any> | undefined | null;
  fieldKey: string;
  editedValues: Record<string, string>;
  onEdit: (key: string, value: string) => void;
  onClear: (key: string) => void;
}

const EditableFieldRow = ({ label, field, fieldKey, editedValues, onEdit, onClear }: EditableFieldRowProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [tempValue, setTempValue] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  const isOverridden = fieldKey in editedValues;
  const originalDisplay = formatValue(field?.valor);
  const displayValue = isOverridden ? editedValues[fieldKey] : originalDisplay;

  // Clases de borde según confianza (solo cuando no está editado manualmente)
  const isBaja = !isOverridden && field?.confianza === "BAJA";
  const isMedia = !isOverridden && field?.confianza === "MEDIA";
  let bgClass = 'border-l-4 border-green-500';
  if (isOverridden) bgClass = 'border-l-4 border-purple-400 bg-purple-50/40';
  else if (isBaja) bgClass = 'bg-red-50/50 border-l-4 border-red-500';
  else if (isMedia) bgClass = 'bg-yellow-50/50 border-l-4 border-yellow-400';

  // Foco automático al activar el modo edición
  useEffect(() => {
    if (isEditing) inputRef.current?.focus();
  }, [isEditing]);

  const handleEditStart = () => {
    setTempValue(displayValue === 'No detectado' ? '' : displayValue);
    setIsEditing(true);
  };

  const handleSave = () => {
    const trimmed = tempValue.trim();
    if (trimmed && trimmed !== originalDisplay) {
      onEdit(fieldKey, trimmed);
    } else if (!trimmed) {
      onClear(fieldKey); // Si borran todo, restaurar original
    }
    setIsEditing(false);
  };

  const handleCancel = () => setIsEditing(false);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSave();
    if (e.key === 'Escape') handleCancel();
  };

  if (!field) return null;

  return (
    <div className={`flex justify-between items-center p-3 border-b border-gray-100 last:border-0 group ${bgClass}`}>
      {/* Etiqueta */}
      <span className="text-sm font-medium text-gray-500 w-1/3 pl-2 flex-shrink-0">{label}</span>

      {/* Valor / Input */}
      <div className="flex items-center space-x-2 w-2/3 justify-end">
        {isEditing ? (
          // ── Modo edición ──
          <div className="flex items-center space-x-1 w-full justify-end">
            <input
              ref={inputRef}
              type="text"
              value={tempValue}
              onChange={e => setTempValue(e.target.value)}
              onKeyDown={handleKeyDown}
              onBlur={handleSave}
              className="text-sm border border-purple-400 rounded px-2 py-0.5 w-full text-right focus:outline-none focus:ring-2 focus:ring-purple-300 bg-white"
              placeholder="Ingresa el valor correcto..."
            />
            <button
              onMouseDown={e => { e.preventDefault(); handleSave(); }}
              className="flex-shrink-0 text-green-600 hover:text-green-800 transition-colors"
              title="Guardar (Enter)"
            >
              <Check size={16} />
            </button>
            <button
              onMouseDown={e => { e.preventDefault(); handleCancel(); }}
              className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
              title="Cancelar (Esc)"
            >
              <X size={16} />
            </button>
          </div>
        ) : (
          // ── Modo lectura ──
          <>
            <span
              className={`text-sm font-semibold truncate ${isBaja ? 'text-red-700' : isOverridden ? 'text-purple-700' : 'text-gray-900'}`}
              title={displayValue}
            >
              {displayValue}
            </span>

            {/* Botón lápiz — visible al hover */}
            <button
              onClick={handleEditStart}
              className="flex-shrink-0 text-gray-300 hover:text-purple-500 opacity-0 group-hover:opacity-100 transition-all duration-150"
              title="Editar este campo manualmente"
            >
              <Pencil size={14} />
            </button>

            {/* Si fue editado, botón para deshacer */}
            {isOverridden && (
              <button
                onClick={() => onClear(fieldKey)}
                className="flex-shrink-0 text-purple-300 hover:text-red-500 transition-colors"
                title="Restaurar valor original del OCR"
              >
                <X size={12} />
              </button>
            )}

            {/* Badge de confianza */}
            <div className="cursor-help flex-shrink-0">
              {isOverridden
                ? <ManualBadge />
                : <ConfidenceBadge level={field.confianza} tooltip={field.estrategia} score={field.score} />
              }
            </div>
          </>
        )}
      </div>
    </div>
  );
};

// ─── Score global ─────────────────────────────────────────────────────────────

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

// ─── Componente Principal ─────────────────────────────────────────────────────

export default function InvoiceResults({ data }: InvoiceResultsProps) {
  const [editedValues, setEditedValues] = useState<Record<string, string>>({});

  const handleEdit = (key: string, value: string) => {
    setEditedValues(prev => ({ ...prev, [key]: value }));
  };
  const handleClear = (key: string) => {
    setEditedValues(prev => {
      const copy = { ...prev };
      delete copy[key];
      return copy;
    });
  };

  const totalEditados = Object.keys(editedValues).length;
  const scoreGlobal = calcularScoreGlobal(data);
  const scoreColor = scoreGlobal >= 80 ? 'text-green-600' : scoreGlobal >= 55 ? 'text-yellow-600' : 'text-red-600';
  const barColor  = scoreGlobal >= 80 ? 'bg-green-500'  : scoreGlobal >= 55 ? 'bg-yellow-400'  : 'bg-red-500';
  const label     = scoreGlobal >= 80 ? 'Alta precisión' : scoreGlobal >= 55 ? 'Precisión media — Revisar campos marcados' : 'Baja precisión — Revisión manual recomendada';

  // Props comunes para cada fila
  const rowProps = { editedValues, onEdit: handleEdit, onClear: handleClear };

  return (
    <div className="w-full bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex flex-col h-full max-h-[700px]">

      {/* Header */}
      <div className="bg-purple-600 text-white px-6 py-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center space-x-2">
          <FileText size={20} />
          <span>Resultados OCR</span>
        </h2>
        <div className="flex items-center space-x-2">
          {totalEditados > 0 && (
            <span className="text-xs bg-yellow-400 text-yellow-900 px-2 py-0.5 rounded-full font-semibold">
              {totalEditados} campo{totalEditados > 1 ? 's' : ''} editado{totalEditados > 1 ? 's' : ''}
            </span>
          )}
          <span className="text-xs bg-purple-500 px-2 py-1 rounded-full font-mono">
            Motor OCR Inteligente
          </span>
        </div>
      </div>

      {/* Cuerpo con scroll */}
      <div className="overflow-y-auto flex-1 p-4 space-y-6">

        {/* Comprobante */}
        <section>
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center space-x-2">
            <FileText size={14} /><span>Datos del Comprobante</span>
          </h3>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            <EditableFieldRow label="Tipo"         field={data.comprobante.tipo}         fieldKey="comprobante.tipo"         {...rowProps} />
            <EditableFieldRow label="Serie/Número" field={data.comprobante.serie_numero} fieldKey="comprobante.serie_numero" {...rowProps} />
            <EditableFieldRow label="Fecha Emisión"field={data.comprobante.fecha_emision}fieldKey="comprobante.fecha_emision"{...rowProps} />
            <EditableFieldRow label="Moneda"       field={data.comprobante.moneda}       fieldKey="comprobante.moneda"       {...rowProps} />
          </div>
        </section>

        {/* Emisor */}
        <section>
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center space-x-2">
            <Building size={14} /><span>Datos del Emisor</span>
          </h3>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            <EditableFieldRow label="RUC"         field={data.emisor.ruc}         fieldKey="emisor.ruc"         {...rowProps} />
            <EditableFieldRow label="Razón Social" field={data.emisor.razon_social} fieldKey="emisor.razon_social" {...rowProps} />
          </div>
        </section>

        {/* Receptor */}
        <section>
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center space-x-2">
            <User size={14} /><span>Datos del Receptor</span>
          </h3>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            <EditableFieldRow label="RUC / DNI"   field={data.receptor.ruc_dni}     fieldKey="receptor.ruc_dni"     {...rowProps} />
            <EditableFieldRow label="Razón Social" field={data.receptor.razon_social} fieldKey="receptor.razon_social" {...rowProps} />
          </div>
        </section>

        {/* Montos */}
        <section>
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2 flex items-center space-x-2">
            <Calculator size={14} /><span>Montos y Totales</span>
          </h3>
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm">
            <EditableFieldRow label="Subtotal"  field={data.montos.subtotal} fieldKey="montos.subtotal" {...rowProps} />
            <EditableFieldRow label="IGV (18%)" field={data.montos.igv}      fieldKey="montos.igv"      {...rowProps} />
            <EditableFieldRow label="Total"     field={data.montos.total}    fieldKey="montos.total"    {...rowProps} />
          </div>
        </section>

      </div>

      {/* Footer: Métrica global */}
      <div className="bg-gray-50 border-t border-gray-200 px-5 py-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Precisión Global OCR</span>
          <span className={`text-sm font-bold ${scoreColor}`}>{scoreGlobal}%</span>
        </div>
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
