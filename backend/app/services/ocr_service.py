import os
import pytesseract
from PIL import Image
import cv2
import numpy as np

try:
    import fitz  # PyMuPDF para manejar PDFs
except ImportError:
    fitz = None

# IMPORTANTE: En Windows a veces necesitas especificar la ruta exacta de Tesseract si no está en las variables de entorno.
# Si tienes un error de "tesseract is not installed", descomenta la siguiente línea y verifica la ruta:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(img: np.ndarray) -> np.ndarray:
    """Aplica filtros avanzados de visión computacional para mejorar el OCR."""
    # 1. Resize: Aumentar resolución (2x) para capturar detalles finos
    img = cv2.resize(img, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
    
    # 2. Escala de Grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 3. Denoise: Reducir ruido de escaneo/foto sin perder bordes
    denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
    
    # 4. Aumento de Contraste
    contrast = cv2.convertScaleAbs(denoised, alpha=1.5, beta=0)
    
    # 5. Binarización de Otsu (convierte a blanco/negro puro óptimo)
    _, thresh = cv2.threshold(contrast, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return thresh

def extract_text_from_image(image_path: str) -> str:
    """
    Extrae texto de una imagen (.png, .jpg) usando Tesseract OCR.
    Incluye un preprocesamiento básico con OpenCV para mejorar la lectura.
    """
    # Leer la imagen con OpenCV
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"No se pudo cargar la imagen: {image_path}")

    # Preprocesamiento Avanzado con OpenCV
    processed_img = preprocess_image(img)
    
    # Extraer texto indicando que el idioma es español
    text = pytesseract.image_to_string(processed_img, lang='spa')
    return text.strip()

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extrae texto de un archivo PDF convirtiendo cada página en imagen
    y pasándola por Tesseract. Requiere instalar PyMuPDF.
    """
    if fitz is None:
        raise ImportError("Falta instalar PyMuPDF para procesar PDFs. Ejecuta: pip install pymupdf")
        
    doc = fitz.open(pdf_path)
    full_text = ""
    
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
        
        # Pasar a Tesseract
        text = pytesseract.image_to_string(processed_img, lang='spa')
        full_text += f"\n--- Página {page_num + 1} ---\n"
        full_text += text
        
    return full_text.strip()

def process_document(file_path: str) -> str:
    """
    Función principal que detecta la extensión y aplica el método correcto.
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
        print(resultado)
        print("\n=================\nFin de la prueba\n=================")
    except Exception as e:
        print(f"Error: {e}")
