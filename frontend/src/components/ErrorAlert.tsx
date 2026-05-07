import { AlertCircle, XCircle } from 'lucide-react';

interface ErrorAlertProps {
  error: string | null;
  onClose: () => void;
}

export default function ErrorAlert({ error, onClose }: ErrorAlertProps) {
  if (!error) return null;

  return (
    <div className="w-full max-w-2xl mx-auto mt-4 animate-in fade-in slide-in-from-top-4 duration-300">
      <div className="bg-red-50 border-l-4 border-red-500 rounded-r-lg p-4 shadow-sm relative">
        <div className="flex items-start">
          <div className="flex-shrink-0">
            <AlertCircle className="h-5 w-5 text-red-500" />
          </div>
          <div className="ml-3 pr-8">
            <h3 className="text-sm font-medium text-red-800">
              Error en el procesamiento
            </h3>
            <p className="mt-1 text-sm text-red-700">
              {error}
            </p>
          </div>
          <button 
            onClick={onClose}
            className="absolute top-4 right-4 text-red-400 hover:text-red-600 transition-colors"
          >
            <XCircle className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
