import React, { useCallback, useState, useRef } from 'react';
import { UploadCloud, File as FileIcon, X, Loader2 } from 'lucide-react';

interface UploadSectionProps {
  onFileSelect: (file: File) => void;
  isLoading: boolean;
}

export default function UploadSection({ onFileSelect, isLoading }: UploadSectionProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      handleFile(file);
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file: File) => {
    // Solo permitimos PDF o Imágenes para este OCR
    if (file.type === "application/pdf" || file.type.startsWith("image/")) {
      setSelectedFile(file);
    } else {
      alert("Por favor, sube un documento PDF o una Imagen.");
    }
  };

  const clearFile = (e: React.MouseEvent) => {
    e.stopPropagation();
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = () => {
    if (selectedFile && !isLoading) {
      onFileSelect(selectedFile);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto mt-8">
      <div 
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ease-in-out cursor-pointer
          ${isDragging ? 'border-purple-500 bg-purple-50' : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'}
          ${isLoading ? 'opacity-50 pointer-events-none' : ''}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !selectedFile && fileInputRef.current?.click()}
      >
        <input 
          type="file" 
          ref={fileInputRef}
          onChange={handleFileInput}
          className="hidden" 
          accept=".pdf,image/*"
        />

        {!selectedFile ? (
          <div className="flex flex-col items-center space-y-4">
            <div className="p-4 bg-purple-100 rounded-full text-purple-600">
              <UploadCloud size={40} />
            </div>
            <div>
              <p className="text-lg font-medium text-gray-700">Arrastra y suelta tu factura aquí</p>
              <p className="text-sm text-gray-500 mt-1">Soporta PDF, PNG o JPG (Max 10MB)</p>
            </div>
            <button className="mt-4 px-6 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
              Explorar archivos
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-4">
            <div className="flex items-center space-x-3 p-4 bg-white border border-gray-200 rounded-lg shadow-sm w-full max-w-md">
              <FileIcon className="text-purple-500" size={24} />
              <div className="flex-1 text-left overflow-hidden">
                <p className="text-sm font-medium text-gray-900 truncate">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              {!isLoading && (
                <button onClick={clearFile} className="text-gray-400 hover:text-red-500 transition-colors">
                  <X size={20} />
                </button>
              )}
            </div>
            
            <button 
              onClick={handleSubmit}
              disabled={isLoading}
              className="mt-4 flex items-center space-x-2 px-8 py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:bg-purple-400"
            >
              {isLoading ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  <span>Procesando con IA...</span>
                </>
              ) : (
                <span>Extraer Datos</span>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
