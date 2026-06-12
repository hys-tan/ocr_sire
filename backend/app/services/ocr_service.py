import os
from PIL import Image
import cv2
import numpy as np
import logging
import pytesseract

try:
    import fitz  # PyMuPDF para manejar PDFs
except ImportError:
    fitz = None

# Configurar logger
logger = logging.getLogger("ExtractorSIRE.OCR")

# Ruta al ejecutable de Tesseract en Windows
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def run_tesseract_and_adapt(img_input) -> dict:
    """
    Ejecuta Tesseract OCR y adapta su salida a nuestro formato de diccionario.
    Recibe una ruta de imagen (str) o un objeto PIL Image / numpy array.
    """
    logger.info("Ejecutando extracción con Tesseract OCR...")
    
    # Si es una ruta, abrir con PIL
    if isinstance(img_input, str):
        img = Image.open(img_input)
    elif isinstance(img_input, np.ndarray):
        img = Image.fromarray(img_input)
    else:
        img = img_input  # Ya es PIL Image
    
    # Usar image_to_data para obtener texto + confianza por palabra
    # lang='spa' para español, config con --psm 6 (bloque de texto uniforme)
    data = pytesseract.image_to_data(
        img, lang='spa', output_type=pytesseract.Output.DICT,
        config='--psm 6'
    )
    
    word_conf_dict = {}
    total_conf = 0
    word_count = 0
    line_texts = {}  # Agrupamos por número de línea
    
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        conf = int(data["conf"][i])
        line_num = data["line_num"][i]
        block_num = data["block_num"][i]
        
        # Tesseract devuelve conf=-1 para separadores vacíos, los ignoramos
        if conf < 0 or not text:
            continue
        
        # Agrupar texto por bloque y línea para reconstruir el documento
        line_key = (block_num, line_num)
        if line_key not in line_texts:
            line_texts[line_key] = []
        line_texts[line_key].append(text)
        
        # Guardar confianza por palabra
        lookup_word = text.lower().strip(".,:-_?¿!¡()[]{}'\"/\\")
        if lookup_word:
            if lookup_word not in word_conf_dict:
                word_conf_dict[lookup_word] = []
            word_conf_dict[lookup_word].append(conf)
            total_conf += conf
            word_count += 1
    
    # Reconstruir texto línea por línea
    sorted_keys = sorted(line_texts.keys())
    reconstructed_lines = [" ".join(line_texts[k]) for k in sorted_keys]
    reconstructed_text = "\n".join(reconstructed_lines)
    
    avg_conf = (total_conf / word_count) if word_count > 0 else 0
    
    logger.info(f"Tesseract finalizado. Confianza promedio: {avg_conf:.2f}%")
    
    return {
        "text": reconstructed_text,
        "word_confidences": word_conf_dict,
        "avg_confidence": avg_conf,
        "engine_used": "tesseract"
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
    
    # Convertir de vuelta a PIL Image (Tesseract trabaja bien con imágenes en escala de grises)
    return Image.fromarray(thresh)

def extract_text_from_image(image_path: str) -> dict:
    """
    Extrae texto de una imagen (.png, .jpg) usando Tesseract + OpenCV.
    Devuelve un diccionario con {"text": ..., "word_confidences": ...}.
    """
    # 1. Preprocesar con OpenCV
    processed_img = preprocess_image_with_opencv(image_path)
    
    # 2. Pasar la imagen limpia a Tesseract
    return run_tesseract_and_adapt(processed_img)

def extract_text_from_pdf(pdf_path: str) -> dict:
    """
    Extrae texto de un archivo PDF convirtiendo cada página en imagen
    y pasándola por Tesseract. Requiere instalar PyMuPDF.
    Devuelve un diccionario con {"text": ..., "word_confidences": ...}.
    """
    if fitz is None:
        raise ImportError("Falta instalar PyMuPDF para procesar PDFs. Ejecuta: pip install pymupdf")
        
    doc = fitz.open(pdf_path)
    full_text = ""
    global_word_conf = {}
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Aumentar la resolución de la imagen (zoom) para ayudar a Tesseract a ver mejor
        zoom_x = 2.0  
        zoom_y = 2.0  
        mat = fitz.Matrix(zoom_x, zoom_y)
        pix = page.get_pixmap(matrix=mat)
        
        # Convertir Pixmap a formato PIL Image
        img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # 1. Preprocesar con OpenCV la imagen extraída del PDF
        processed_img = preprocess_image_with_opencv(img_pil)
        
        # 2. Enviar a Tesseract
        page_result = run_tesseract_and_adapt(processed_img)
        
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
    print("=== PRUEBA DE OCR (TESSERACT + OPENCV) ===")
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
