import { useState } from 'react';
import UploadSection from './components/UploadSection';
import PDFViewer from './components/PDFViewer';
import InvoiceResults from './components/InvoiceResults';
import OCRMetrics from './components/OCRMetrics';
import LoadingOverlay from './components/LoadingOverlay';
import ErrorAlert from './components/ErrorAlert';
import { extractInvoiceData } from './services/api';
import type { InvoiceResponse } from './types/invoice';

export default function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [invoiceData, setInvoiceData] = useState<InvoiceResponse | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileSelect = async (file: File) => {
    setIsLoading(true);
    setError(null);
    setSelectedFile(file);
    try {
      console.log("Enviando archivo al OCR:", file.name);
      const data = await extractInvoiceData(file);
      console.log("¡Datos recibidos exitosamente!", data);
      setInvoiceData(data);
    } catch (err: any) {
      setError(err.message || "Error al procesar el archivo");
      alert("Error al comunicarse con el Backend.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setInvoiceData(null);
    setSelectedFile(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className={invoiceData ? "max-w-7xl mx-auto" : "max-w-4xl mx-auto mt-12"}>
        
        {/* Cabecera */}
        <div className="text-center mb-8 relative">
          <h1 className="text-4xl font-bold text-gray-900 tracking-tight">
            OCR SIRE
          </h1>
          <p className="mt-2 text-gray-500">
            Sistema Inteligente de Extracción de Datos
          </p>
          
          {invoiceData && (
            <button 
              onClick={handleReset}
              className="absolute right-0 top-2 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg text-sm font-medium transition-colors"
            >
              Procesar otro documento
            </button>
          )}
        </div>
        
        <ErrorAlert error={error} onClose={() => setError(null)} />
        
        {/* Vista Condicional */}
        {!invoiceData || !selectedFile ? (
          <UploadSection 
            onFileSelect={handleFileSelect} 
            isLoading={isLoading} 
          />
        ) : (
          <div className="flex flex-col lg:flex-row gap-6 mt-6 items-start h-full">
            {/* Mitad Izquierda: PDF */}
            <div className="w-full lg:w-1/2 sticky top-6">
              <PDFViewer file={selectedFile} />
            </div>
            
            {/* Mitad Derecha: Resultados + Métricas */}
            <div className="w-full lg:w-1/2 flex flex-col gap-4">
              <InvoiceResults data={invoiceData} />
              <OCRMetrics metricas={invoiceData.metricas} />
            </div>
          </div>
        )}
      </div>
      
      <LoadingOverlay isVisible={isLoading} />
    </div>
  )
}
