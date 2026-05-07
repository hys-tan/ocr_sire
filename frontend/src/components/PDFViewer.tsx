import { useEffect, useState } from 'react';

interface PDFViewerProps {
  file: File;
}

export default function PDFViewer({ file }: PDFViewerProps) {
  const [fileUrl, setFileUrl] = useState<string>('');

  useEffect(() => {
    const url = URL.createObjectURL(file);
    setFileUrl(url);
    
    // Limpieza para evitar fugas de memoria
    return () => URL.revokeObjectURL(url);
  }, [file]);

  if (!fileUrl) return null;

  return (
    <div className="w-full h-full min-h-[700px] bg-gray-100 rounded-xl overflow-hidden border border-gray-200 shadow-sm flex flex-col">
      <div className="bg-gray-800 text-gray-200 text-xs px-4 py-2 font-mono flex justify-between items-center">
        <span>Visor de Documento</span>
        <span>{file.name}</span>
      </div>
      <div className="flex-1">
        {file.type === "application/pdf" ? (
          <iframe 
            src={`${fileUrl}#toolbar=0`} 
            className="w-full h-full min-h-[660px]" 
            title="Visor PDF" 
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center p-4 bg-gray-50">
            <img 
              src={fileUrl} 
              alt="Documento" 
              className="max-w-full max-h-[660px] object-contain rounded shadow-sm" 
            />
          </div>
        )}
      </div>
    </div>
  );
}
