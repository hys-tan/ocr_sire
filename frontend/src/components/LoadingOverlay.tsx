import { Loader2 } from 'lucide-react';

interface LoadingOverlayProps {
  isVisible: boolean;
  message?: string;
}

export default function LoadingOverlay({ isVisible, message = "Procesando documento con IA..." }: LoadingOverlayProps) {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 flex items-center justify-center transition-opacity duration-300">
      <div className="bg-white rounded-2xl p-8 shadow-2xl flex flex-col items-center max-w-sm w-full mx-4 transform transition-all duration-300 scale-100">
        <div className="relative">
          <div className="absolute inset-0 bg-purple-200 rounded-full animate-ping opacity-75"></div>
          <div className="relative bg-purple-100 text-purple-600 p-4 rounded-full">
            <Loader2 className="animate-spin" size={40} />
          </div>
        </div>
        <h3 className="mt-6 text-lg font-semibold text-gray-900 text-center">
          Analizando Documento
        </h3>
        <p className="mt-2 text-sm text-gray-500 text-center">
          {message}
        </p>
      </div>
    </div>
  );
}
