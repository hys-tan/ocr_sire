import { useEffect, useState } from 'react';
import { ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface PDFViewerProps {
  file: File;
}

const ZOOM_STEP = 25;   // % por paso
const ZOOM_MIN  = 50;
const ZOOM_MAX  = 300;
const ZOOM_INIT = 100;

export default function PDFViewer({ file }: PDFViewerProps) {
  const [fileUrl, setFileUrl] = useState<string>('');
  const [zoom, setZoom]       = useState<number>(ZOOM_INIT);

  const isImage = file.type.startsWith('image/');

  useEffect(() => {
    const url = URL.createObjectURL(file);
    setFileUrl(url);
    setZoom(ZOOM_INIT);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  if (!fileUrl) return null;

  const zoomIn    = () => setZoom(z => Math.min(z + ZOOM_STEP, ZOOM_MAX));
  const zoomOut   = () => setZoom(z => Math.max(z - ZOOM_STEP, ZOOM_MIN));
  const zoomReset = () => setZoom(ZOOM_INIT);

  return (
    <div className="w-full h-full min-h-[700px] bg-gray-100 rounded-xl overflow-hidden border border-gray-200 shadow-sm flex flex-col">

      {/* Barra superior */}
      <div className="bg-gray-800 text-gray-200 text-xs px-4 py-2 font-mono flex justify-between items-center flex-shrink-0">
        <span>Visor de Documento</span>

        <div className="flex items-center space-x-1">
          {/* Controles de zoom — solo para imágenes; PDF usa toolbar nativo */}
          {isImage && (
            <>
              <button
                onClick={zoomOut}
                disabled={zoom <= ZOOM_MIN}
                className="p-1 rounded hover:bg-gray-600 disabled:opacity-30 transition-colors"
                title="Reducir zoom"
              >
                <ZoomOut size={14} />
              </button>

              <button
                onClick={zoomReset}
                className="px-2 py-0.5 rounded hover:bg-gray-600 transition-colors tabular-nums min-w-[42px] text-center"
                title="Restablecer zoom (100%)"
              >
                {zoom}%
              </button>

              <button
                onClick={zoomIn}
                disabled={zoom >= ZOOM_MAX}
                className="p-1 rounded hover:bg-gray-600 disabled:opacity-30 transition-colors"
                title="Aumentar zoom"
              >
                <ZoomIn size={14} />
              </button>

              {zoom !== ZOOM_INIT && (
                <button
                  onClick={zoomReset}
                  className="p-1 rounded hover:bg-gray-600 transition-colors ml-1"
                  title="Restablecer"
                >
                  <RotateCcw size={12} />
                </button>
              )}

              <span className="mx-2 text-gray-600">|</span>
            </>
          )}

          <span className="text-gray-400 truncate max-w-[200px]">{file.name}</span>
        </div>
      </div>

      {/* Contenido */}
      <div className="flex-1 overflow-auto">
        {!isImage ? (
          /*
           * PDF: se muestra el toolbar nativo del browser.
           * Eso incluye zoom real (+/-/porcentaje), ajuste de página,
           * navegación entre páginas y búsqueda de texto.
           */
          <iframe
            src={fileUrl}
            className="w-full h-full min-h-[660px]"
            title="Visor PDF"
          />
        ) : (
          /*
           * Imagen: zoom mediante width real (no transform).
           * Al cambiar el width el elemento crece en el DOM →
           * el scroll del contenedor aparece de forma natural.
           */
          <div className="w-full min-h-[660px] overflow-auto p-4 bg-gray-50">
            <img
              src={fileUrl}
              alt="Documento"
              style={{ width: `${zoom}%`, display: 'block', transition: 'width 0.15s ease' }}
              className="object-contain rounded shadow-sm mx-auto"
              draggable={false}
            />
          </div>
        )}
      </div>

    </div>
  );
}
