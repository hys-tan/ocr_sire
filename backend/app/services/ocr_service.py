import os
from PIL import Image
import cv2
import numpy as np
import logging

try:
    import fitz  # PyMuPDF para manejar PDFs
except ImportError:
    fitz = None

# Configurar logger
logger = logging.getLogger("ExtractorSIRE.OCR")

_paddle_engine = None

def get_paddle_engine():
    """Carga Perezosa (Lazy Loading) de PaddleOCR para no afectar el inicio del backend."""
    global _paddle_engine
    if _paddle_engine is None:
        logger.info("Inicializando motor PaddleOCR por primera vez (esto puede tardar unos segundos)...")
        from paddleocr import PaddleOCR
        # use_angle_cls=True permite detectar texto rotado. lang='es' para español.
        # show_log=False evita que Paddle inunde la consola con mensajes DEBUG
        _paddle_engine = PaddleOCR(use_angle_cls=True, lang='es', show_log=False)
        logger.info("PaddleOCR inicializado correctamente.")
    return _paddle_engine

def run_paddleocr_and_adapt(img_path_or_array) -> dict:
    """
    Ejecuta PaddleOCR y adapta su salida a nuestro formato de diccionario.
    """
    engine = get_paddle_engine()
    logger.info("Ejecutando extracción profunda con PaddleOCR...")
    
    # Ejecutar PaddleOCR. Devuelve una lista de resultados por línea detectada.
    result = engine.ocr(img_path_or_array, cls=True)
    
    reconstructed_text = ""
    word_conf_dict = {}
    total_conf = 0
    word_count = 0
    
    # result puede ser None o una lista que contiene una lista (por página)
    if not result or not result[0]:
        return {
            "text": "",
            "word_confidences": {},
            "avg_confidence": 0,
            "engine_used": "paddleocr"
        }
        
    line_texts = []
    
    for idx, line in enumerate(result[0]):
        # line tiene el formato: [[caja delimitadora], (texto, confianza)]
        box = line[0]
        text_tuple = line[1]
        text = text_tuple[0]
        # PaddleOCR devuelve la confianza de 0.0 a 1.0. 
        confidence = int(float(text_tuple[1]) * 100)
        
        # Limpiar texto
        text_clean = text.strip()
        if not text_clean:
            continue
            
        line_texts.append(text_clean)
        
        # Dividir la frase detectada en palabras para el diccionario
        words = text_clean.split()
        for w in words:
            lookup_word = w.lower().strip(".,:-_?¿!¡()[]{}'\"/\\")
            if lookup_word:
                if lookup_word not in word_conf_dict:
                    word_conf_dict[lookup_word] = []
                word_conf_dict[lookup_word].append(confidence)
                total_conf += confidence
                word_count += 1
                
    reconstructed_text = "\n".join(line_texts)
    avg_conf = (total_conf / word_count) if word_count > 0 else 0
    
    logger.info(f"PaddleOCR finalizado. Confianza promedio: {avg_conf:.2f}%")
    
    return {
        "text": reconstructed_text,
        "word_confidences": word_conf_dict,
        "avg_confidence": avg_conf,
        "engine_used": "paddleocr"
    }

def preprocess_image_with_opencv(img_input):
    """
    Aplica técnicas de Visión Computacional (OpenCV) para limpiar 
    la imagen antes de enviarla al OCR.
    """
    logger.info("Aplicando filtros de OpenCV (Grises + GaussianBlur + Otsu Binarization)...")
    
    if isinstance(img_input, str):
        img = cv2.imread(img_input)
    else:
        img = np.array(img_input)
        # Convertir RGB de PIL a BGR de OpenCV si es necesario
        if len(img.shape) == 3 and img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
    if img is None:
        raise ValueError("No se pudo cargar la imagen para OpenCV.")

    # 1. Escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Reducción leve de ruido
    blur = cv2.GaussianBlur(gray, (3,3), 0)
    
    # 3. Binarización Otsu (muy efectiva para contrastar letras negras sobre fondo blanco/gris)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Como PaddleOCR espera idealmente 3 canales, convertimos la binaria de vuelta a RGB
    # Esto evita problemas internos del motor
    thresh_rgb = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)
    
    return thresh_rgb

def extract_text_from_image(image_path: str) -> dict:
    """
    Extrae texto de una imagen (.png, .jpg) usando PaddleOCR + OpenCV.
    Devuelve un diccionario con {"text": ..., "word_confidences": ...}.
    """
    # 1. Preprocesar con OpenCV
    processed_img = preprocess_image_with_opencv(image_path)
    
    # 2. Pasar la imagen limpia a PaddleOCR
    return run_paddleocr_and_adapt(processed_img)

def extract_text_from_pdf(pdf_path: str) -> dict:
    """
    Extrae texto de un archivo PDF convirtiendo cada página en imagen
    y pasándola por PaddleOCR. Requiere instalar PyMuPDF.
    Devuelve un diccionario con {"text": ..., "word_confidences": ...}.
    """
    if fitz is None:
        raise ImportError("Falta instalar PyMuPDF para procesar PDFs. Ejecuta: pip install pymupdf")
        
    doc = fitz.open(pdf_path)
    full_text = ""
    global_word_conf = {}
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Aumentar la resolución de la imagen (zoom) para ayudar a PaddleOCR a ver mejor
        zoom_x = 2.0  
        zoom_y = 2.0  
        mat = fitz.Matrix(zoom_x, zoom_y)
        pix = page.get_pixmap(matrix=mat)
        
        # Convertir Pixmap a formato PIL Image
        img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # 1. Preprocesar con OpenCV la imagen extraída del PDF
        processed_img = preprocess_image_with_opencv(img_pil)
        
        # 2. Enviar a PaddleOCR
        page_result = run_paddleocr_and_adapt(processed_img)
        
        full_text += f"\n--- Página {page_num + 1} ---\n"
        full_text += page_result["text"]
        
        # Combinar confianzas de palabras de esta página
        for word, confs in page_result["word_confidences"].items():
            if word not in global_word_conf:
                global_word_conf[word] = []
            global_word_conf[word].extend(confs)
        
    return {
        "text": full_text.strip(),
        "word_confidences": global_word_conf
    }

def process_document(file_path: str) -> dict:
    """
    Función principal que detecta la extensión, aplica el método correcto
    y devuelve un diccionario con {"text": ..., "word_confidences": ...}.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"El archivo no existe: {file_path}")
        
    ext = file_path.lower().split('.')[-1]
    
    if ext in ['png', 'jpg', 'jpeg']:
        return extract_text_from_image(file_path)
    elif ext == 'pdf':
        return extract_text_from_pdf(file_path)
    else:
        raise ValueError(f"Formato no soportado: {ext}. Usa PNG, JPG o PDF.")

# --- PRUEBA LOCAL ---
if __name__ == "__main__":
    print("=== PRUEBA DE OCR (PADDLEOCR + OPENCV) ===")
    print("Coloca una imagen o PDF en la carpeta 'assets' y cambia la ruta aquí abajo.")
    
    # Ruta relativa al directorio donde ejecutas el script (carpeta backend)
    test_file = "assets/prueba2.pdf" 
    
    try:
        resultado = process_document(test_file)
        print("Texto extraído:\n")
        print(resultado["text"])
        print("\n=================\nFin de la prueba\n=================")
    except Exception as e:
        print(f"Error: {e}")
