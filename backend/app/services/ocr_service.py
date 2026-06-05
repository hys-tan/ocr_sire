import os
import pytesseract
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

# IMPORTANTE: En Windows a veces necesitas especificar la ruta exacta de Tesseract si no está en las variables de entorno.
# Si tienes un error de "tesseract is not installed", descomenta la siguiente línea y verifica la ruta:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def deskew_image(img: np.ndarray) -> np.ndarray:
    """Endereza una imagen si está inclinada."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
    # Binarizar invertido para que el texto sea blanco y el fondo negro
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    
    # Encontrar todas las coordenadas de píxeles distintos de cero (el texto)
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) == 0:
        return img
        
    angle = cv2.minAreaRect(coords)[-1]
    
    # Ajustar el ángulo obtenido por minAreaRect para la rotación correcta
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    # Solo rotar si la inclinación es notable (entre 0.5 y 45 grados)
    if abs(angle) < 0.5 or abs(angle) > 45:
        return img
        
    logger.info(f"Deskew: Detectada inclinación de {angle:.2f} grados. Enderezando imagen...")
    
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    
    return rotated

def preprocess_image(img: np.ndarray) -> np.ndarray:
    """Aplica filtros avanzados de visión computacional para mejorar el OCR."""
    # 1. Enderezar la imagen (Deskew)
    img_deskewed = deskew_image(img)
    
    # 2. Resize: Aumentar resolución (2x) para capturar detalles finos
    resized = cv2.resize(img_deskewed, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    
    # 3. Escala de Grises
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    
    # 4. Denoise: Reducir ruido de escaneo/foto sin perder bordes
    denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
    
    # 5. CLAHE: Mejora local y adaptativa del contraste
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast = clahe.apply(denoised)
    
    # 6. Binarización Adaptativa (Gaussian Thresholding) en lugar de Otsu
    thresh = cv2.adaptiveThreshold(
        contrast, 
        255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        11, 
        2
    )
    
    return thresh

def run_tesseract_with_dynamic_psm(processed_img: np.ndarray) -> dict:
    """
    Ejecuta Tesseract con PSM Dinámico (intenta --psm 6, luego --psm 4 y --psm 11).
    Devuelve un diccionario con el texto reconstruido y las confianzas de las palabras.
    """
    psm_modes = ['--psm 6', '--psm 4', '--psm 11']
    best_result = None
    best_avg_conf = -1

    for psm in psm_modes:
        try:
            logger.info(f"Probando Tesseract con modo {psm}...")
            data = pytesseract.image_to_data(
                processed_img, 
                lang='spa', 
                config=psm, 
                output_type=pytesseract.Output.DICT
            )
            
            # Filtrar palabras válidas y calcular confianza promedio
            confidences = []
            word_conf = {}
            lines_map = {}
            
            for i in range(len(data['text'])):
                word = data['text'][i]
                conf_val = data['conf'][i]
                
                try:
                    conf = int(conf_val)
                except (ValueError, TypeError):
                    conf = -1
                
                if conf == -1:
                    continue
                
                word_clean = word.strip()
                if not word_clean:
                    continue
                
                confidences.append(conf)
                
                # Agrupar para reconstruir texto por líneas
                block = data['block_num'][i]
                par = data['par_num'][i]
                line = data['line_num'][i]
                key = (block, par, line)
                if key not in lines_map:
                    lines_map[key] = []
                lines_map[key].append(word_clean)
                
                # Guardar confianza de palabra
                lookup_word = word_clean.lower().strip(".,:-_?¿!¡()[]{}'\"/\\")
                if lookup_word:
                    if lookup_word not in word_conf:
                        word_conf[lookup_word] = []
                    word_conf[lookup_word].append(conf)
            
            avg_conf = sum(confidences) / len(confidences) if confidences else 0
            logger.info(f"Modo {psm} finalizado. Palabras: {len(confidences)}, Confianza promedio: {avg_conf:.2f}%")
            
            # Reconstruir texto
            line_texts = []
            for key in sorted(lines_map.keys()):
                line_words = lines_map[key]
                line_str = " ".join(line_words).strip()
                if line_str:
                    line_texts.append(line_str)
            reconstructed_text = "\n".join(line_texts)
            
            result = {
                "text": reconstructed_text,
                "word_confidences": word_conf,
                "avg_confidence": avg_conf,
                "psm_used": psm
            }
            
            # Si la confianza promedio es alta (>= 50%), aceptamos el resultado de inmediato
            if avg_conf >= 50:
                logger.info(f"Confianza suficiente ({avg_conf:.2f}% >= 50%). Seleccionado {psm}.")
                return result
                
            # Si es menor a 50%, guardamos el mejor resultado
            if avg_conf > best_avg_conf:
                best_avg_conf = avg_conf
                best_result = result
                
        except Exception as e:
            logger.error(f"Error al procesar con Tesseract {psm}: {e}")
            
    # Si ninguno superó el 50%, devolvemos el que tuvo mayor confianza promedio
    if best_result:
        logger.warning(f"Ningún modo superó el 50% de confianza. Seleccionando el mejor: {best_result['psm_used']} con {best_result['avg_confidence']:.2f}%")
        return best_result
        
    return {
        "text": "",
        "word_confidences": {},
        "avg_confidence": 0,
        "psm_used": "--psm 6"
    }

def extract_text_from_image(image_path: str) -> dict:
    """
    Extrae texto de una imagen (.png, .jpg) usando Tesseract OCR con PSM dinámico.
    Devuelve un diccionario con {"text": ..., "word_confidences": ...}.
    """
    # Leer la imagen con OpenCV
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"No se pudo cargar la imagen: {image_path}")

    # Preprocesamiento Avanzado con OpenCV
    processed_img = preprocess_image(img)
    
    # Extraer texto y confianzas con PSM dinámico
    return run_tesseract_with_dynamic_psm(processed_img)

def extract_text_from_pdf(pdf_path: str) -> dict:
    """
    Extrae texto de un archivo PDF convirtiendo cada página en imagen
    y pasándola por Tesseract con PSM dinámico. Requiere instalar PyMuPDF.
    Devuelve un diccionario con {"text": ..., "word_confidences": ...}.
    """
    if fitz is None:
        raise ImportError("Falta instalar PyMuPDF para procesar PDFs. Ejecuta: pip install pymupdf")
        
    doc = fitz.open(pdf_path)
    full_text = ""
    global_word_conf = {}
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Aumentar la resolución de la imagen (zoom)
        zoom_x = 2.0  
        zoom_y = 2.0  
        mat = fitz.Matrix(zoom_x, zoom_y)
        pix = page.get_pixmap(matrix=mat)
        
        # Convertir Pixmap a formato PIL Image
        img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # Convertir de PIL (RGB) a OpenCV (BGR)
        img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        
        # Aplicar el Pipeline de Preprocesamiento
        processed_img = preprocess_image(img_cv)
        
        # Pasar a Tesseract con PSM dinámico
        page_result = run_tesseract_with_dynamic_psm(processed_img)
        
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
    print("=== PRUEBA DE OCR ===")
    print("Coloca una imagen o PDF en la carpeta 'assets' y cambia la ruta aquí abajo.")
    
    # Ruta relativa al directorio donde ejecutas el script (carpeta backend)
    test_file = "assets/prueba2.pdf" 
    
    try:
        resultado = process_document(test_file)
        print("Texto extraído:\n")
        print(resultado["text"])
        print("\nConfianza de algunas palabras:")
        sample_words = list(resultado["word_confidences"].keys())[:10]
        for w in sample_words:
            print(f"  '{w}': {resultado['word_confidences'][w]}")
        print("\n=================\nFin de la prueba\n=================")
    except Exception as e:
        print(f"Error: {e}")
