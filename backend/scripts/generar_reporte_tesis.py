import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración visual para tesis académica
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'sans-serif'

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATASET_DIR = os.path.join(BASE_DIR, "test", "dataset")
REPORTES_DIR = os.path.join(BASE_DIR, "test", "reportes")

# Crear carpeta de reportes si no existe
os.makedirs(REPORTES_DIR, exist_ok=True)

# 1. Archivos de extracción final (Regex vs Ground Truth)
extraction_files = {
    "Tesseract Puro": "metrics_tesseract_base.csv",
    "Tesseract + OpenCV": "metrics_tesseract_opencv.csv",
    "PaddleOCR + OpenCV": "metrics_paddleocr_opencv.csv",
    "PaddleOCR Puro": "metrics_paddleocr_base.csv"
}

# 2. Archivos de reconocimiento óptico puro (Motor OCR vs Ground Truth)
optical_files = {
    "Tesseract Puro": "metrics_tesseract_optico.csv",
    "Tesseract + OpenCV": "metrics_tesseract_opencv_optico.csv",
    "PaddleOCR + OpenCV": "metrics_paddle_opencv_optico.csv",
    "PaddleOCR Puro": "metrics_paddleocr_optico.csv"
}

def analyze_extraction():
    results = []
    for model_name, filename in extraction_files.items():
        filepath = os.path.join(DATASET_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Warning: {filename} no encontrado.")
            continue
        df = pd.read_csv(filepath)
        global_acc = df["Precision_Global_Porcentaje"].mean()
        high_acc = df[df["Calidad"].str.lower() == "alta"]["Precision_Global_Porcentaje"].mean()
        low_acc = df[df["Calidad"].str.lower() == "baja"]["Precision_Global_Porcentaje"].mean()
        results.append({
            "Motor": model_name,
            "Global": global_acc,
            "Alta Calidad": high_acc,
            "Baja Calidad": low_acc
        })
    return pd.DataFrame(results)

def analyze_optical():
    results = []
    for model_name, filename in optical_files.items():
        filepath = os.path.join(DATASET_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Warning: {filename} no encontrado.")
            continue
        df = pd.read_csv(filepath)
        global_acc = df["Acierto"].mean() * 100
        high_acc = df[df["Calidad"].str.lower() == "alta"]["Acierto"].mean() * 100
        low_acc = df[df["Calidad"].str.lower() == "baja"]["Acierto"].mean() * 100
        results.append({
            "Motor": model_name,
            "Global": global_acc,
            "Alta Calidad": high_acc,
            "Baja Calidad": low_acc
        })
    return pd.DataFrame(results)

def generate_chart(df, title, filename):
    if df.empty:
        return
    df_melt = df.melt(id_vars="Motor", var_name="Métrica", value_name="Precisión (%)")
    plt.figure(figsize=(11, 6))
    
    # Paleta de colores profesional
    ax = sns.barplot(data=df_melt, x="Motor", y="Precisión (%)", hue="Métrica", palette="Blues_d")
    
    plt.title(title, fontsize=16, fontweight="bold", pad=15)
    plt.ylim(0, 115)
    plt.ylabel("Precisión Promedio (%)", fontsize=12)
    plt.xlabel("Arquitectura del OCR", fontsize=12)
    plt.xticks(fontsize=11)
    
    # Mover la leyenda afuera
    plt.legend(bbox_to_anchor=(1.01, 1), borderaxespad=0, title="Sub-métrica")
    
    # Añadir los porcentajes encima de las barras
    for p in ax.patches:
        height = p.get_height()
        if pd.notnull(height):
            ax.annotate(f"{height:.1f}%", 
                        (p.get_x() + p.get_width() / 2., height), 
                        ha='center', va='bottom', 
                        fontsize=10, xytext=(0, 5), 
                        textcoords='offset points')
                    
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTES_DIR, filename), dpi=300)
    plt.close()

if __name__ == "__main__":
    print("Analizando métricas y generando gráficos para tesis...")
    
    df_ext = analyze_extraction()
    df_opt = analyze_optical()
    
    print("\n--- Precisión Óptica (Motor OCR) ---")
    print(df_opt)
    
    print("\n--- Precisión de Extracción (OCR + RegEx) ---")
    print(df_ext)
    
    generate_chart(df_opt, "Comparativa de Precisión de Reconocimiento Óptico", "comparativa_optica.png")
    generate_chart(df_ext, "Comparativa de Precisión de Extracción Estructurada", "comparativa_extraccion.png")
    
    print(f"\n¡Gráficos generados con éxito en {REPORTES_DIR}!")
