import { useEffect, useState } from 'react';
import { TransformWrapper, TransformComponent, useControls } from 'react-zoom-pan-pinch';
import { ZoomIn, ZoomOut } from 'lucide-react';

interface PDFViewerProps {
  file: File;
}

// ─── Controles de zoom (deben vivir dentro de TransformWrapper) ───────────────

const ImageZoomControls = () => {
  const { zoomIn, zoomOut, resetTransform } = useControls();
  return (
    <div className="flex items-center space-x-1">
      <button
        onClick={() => zoomOut()}
        className="p-1 rounded hover:bg-gray-600 transition-colors"
        title="Reducir zoom"
      >
        <ZoomOut size={14} />
      </button>
      <button
        onClick={() => resetTransform()}
        className="px-2 py-0.5 rounded hover:bg-gray-600 transition-colors text-xs"
        title="Restablecer zoom"
      >
        Reset
      </button>
      <button
        onClick={() => zoomIn()}
        className="p-1 rounded hover:bg-gray-600 transition-colors"
        title="Aumentar zoom"
      >
        <ZoomIn size={14} />
      </button>
    </div>
  );
};

// ─── Componente principal ─────────────────────────────────────────────────────

export default function PDFViewer({ file }: PDFViewerProps) {
  const [fileUrl, setFileUrl] = useState<string>('');

  const isImage = file.type.startsWith('image/');

  useEffect(() => {
    const url = URL.createObjectURL(file);
    setFileUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  if (!fileUrl) return null;

  return (
    <div className="w-full h-full min-h-[700px] bg-gray-100 rounded-xl overflow-hidden border border-gray-200 shadow-sm flex flex-col">

      {isImage ? (
        /*
         * IMAGEN: TransformWrapper envuelve tanto los controles como el contenido
         * para que useControls() tenga acceso al contexto.
         */
        <TransformWrapper
          initialScale={1}
          minScale={0.3}
          maxScale={5}
          doubleClick={{ mode: 'zoomIn' }}
        >
          {/* Barra superior con controles de zoom */}
          <div className="bg-gray-800 text-gray-200 text-xs px-4 py-2 font-mono flex justify-between items-center flex-shrink-0">
            <span>Visor de Documento</span>
            <div className="flex items-center space-x-2">
              <ImageZoomControls />
              <span className="mx-1 text-gray-600">|</span>
              <span className="text-gray-400 truncate max-w-[200px]">{file.name}</span>
            </div>
          </div>

          {/* Área de imagen con zoom/pan */}
          <div className="flex-1 overflow-hidden bg-gray-50">
            <TransformComponent
              wrapperStyle={{ width: '100%', height: '100%', minHeight: '660px' }}
              contentStyle={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'flex-start', padding: '16px' }}
            >
              <img
                src={fileUrl}
                alt="Documento"
                style={{ maxWidth: '100%', objectFit: 'contain', borderRadius: '4px' }}
                draggable={false}
              />
            </TransformComponent>
          </div>
        </TransformWrapper>
      ) : (
        /*
         * PDF: toolbar nativo del browser (zoom, navegación, búsqueda).
         * Se quitó #toolbar=0 para exponer los controles nativos.
         */
        <>
          <div className="bg-gray-800 text-gray-200 text-xs px-4 py-2 font-mono flex justify-between items-center flex-shrink-0">
            <span>Visor de Documento</span>
            <span className="text-gray-400 truncate max-w-[200px]">{file.name}</span>
          </div>
          <div className="flex-1">
            <iframe
              src={fileUrl}
              className="w-full h-full min-h-[660px]"
              title="Visor PDF"
            />
          </div>
        </>
      )}

    </div>
  );
}
