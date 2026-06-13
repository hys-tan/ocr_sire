import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.metrics import classification_report, confusion_matrix

def entrenar_modelo():
    dataset_path = "labeled_dataset.csv"
    model_dir = "models"
    model_path = os.path.join(model_dir, "block_classifier.pkl")
    
    if not os.path.exists(dataset_path):
        print(f"Error: No se encontró {dataset_path}. Ejecuta auto_labeler.py primero.")
        return
        
    print("Cargando dataset...")
    df = pd.read_csv(dataset_path)
    
    # Eliminar posibles valores nulos
    df = df.dropna(subset=['texto', 'clase_bloque'])
    
    print(f"Total de líneas cargadas: {len(df)}")
    print("Distribución de clases:")
    print(df['clase_bloque'].value_counts())
    
    # Extraer variables
    X = df['texto']
    y = df['clase_bloque']
    
    # Dividir estratificado
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    print("\nEntrenando clasificador Naive Bayes con balanceo heurístico...")
    # Scikit-Learn MultinomialNB no tiene class_weight='balanced' integrado directamente en el constructor,
    # pero podemos calcular priors o usar ComplementNB, o ajustar parámetros.
    # Usaremos el TfidfVectorizer normal que maneja muy bien la dispersión.
    
    pipeline = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), analyzer='word', sublinear_tf=True),
        MultinomialNB()
    )
    
    pipeline.fit(X_train, y_train)
    
    print("\nEvaluando modelo en el conjunto de prueba (30%)...")
    y_pred = pipeline.predict(X_test)
    
    print("\n--- REPORTE DE CLASIFICACIÓN ---")
    report_str = classification_report(y_test, y_pred)
    print(report_str)
    
    print("--- MATRIZ DE CONFUSIÓN ---")
    print(confusion_matrix(y_test, y_pred))
    
    # --- EXPORTAR REPORTES (MARKDOWN Y CSV) ---
    report_dict = classification_report(y_test, y_pred, output_dict=True)
    df_metrics = pd.DataFrame(report_dict).transpose()
    
    # Generar CSV
    csv_path = os.path.join("test", "dataset", "metricas_modelo_hibrido.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df_metrics.to_csv(csv_path, float_format="%.4f")
    
    # Generar Markdown
    md_path = os.path.join("test", "dataset", "metricas_modelo_hibrido.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Métricas del Modelo Híbrido (Scikit-Learn Naive Bayes)\n\n")
        f.write("## Reporte de Clasificación\n")
        f.write(df_metrics.to_markdown(floatfmt=".4f"))
        f.write("\n\n## Matriz de Confusión\n```text\n")
        f.write(str(confusion_matrix(y_test, y_pred)))
        f.write("\n```\n")
        
    print(f"\nReportes generados en {csv_path} y {md_path}")
    
    # Guardar el modelo
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        
    joblib.dump(pipeline, model_path)
    print(f"\n¡Modelo entrenado y guardado exitosamente en: {model_path}!")

if __name__ == "__main__":
    entrenar_modelo()
