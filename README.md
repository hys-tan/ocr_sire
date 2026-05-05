# 🧾 Sistema OCR y Clasificación Automática para SIRE

## 📌 Descripción del Proyecto

Este proyecto implementa un sistema basado en **OCR (Reconocimiento Óptico de Caracteres)** y **Machine Learning** para automatizar el registro de información contable en el SIRE.

El sistema permite procesar documentos como facturas en PDF o imágenes, extraer información relevante y clasificarla automáticamente.

---

## 🎯 Objetivos

### Objetivo General

Desarrollar un sistema OCR con clasificación automática para optimizar el registro de comprobantes en el SIRE.

### Objetivos Específicos

* Extraer texto desde documentos mediante OCR
* Procesar y limpiar la información
* Identificar datos clave (RUC, fechas, montos)
* Clasificar documentos automáticamente
* Implementar una interfaz web

---

## 🧠 Tecnologías Utilizadas

### Backend

* Python
* FastAPI
* Tesseract OCR
* OpenCV
* spaCy
* Scikit-learn

### Frontend

* React (en desarrollo)

---

## 🏗️ Estructura del Proyecto

```
ocr_sire/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   └── ocr_service.py
│   │   └── main.py
│   │
│   ├── assets/
│   │   └── prueba.pdf
│   │
│   ├── requirements.txt
│   └── venv/
│
├── frontend/
├── LICENSE
└── README.md
```

---

## 📂 Uso de la carpeta `assets`

La carpeta `assets/` se utiliza para almacenar documentos de prueba (facturas, PDFs, imágenes).

⚠️ **Importante:**

* Esta carpeta puede contener información sensible
* Por ello, su contenido está excluido del control de versiones (`.gitignore`)

### 📌 Configuración

1. Crear la carpeta si no existe:

```
backend/assets/
```

2. Colocar dentro los archivos a procesar (PDF o imágenes)

3. El sistema utilizará estos archivos para pruebas de OCR

---

## ⚙️ Instalación y Configuración

### 1. Clonar repositorio

```
git clone https://github.com/hys-tan/ocr_sire.git
cd ocr_sire
```

---

### 2. Configurar entorno (Backend)

```
cd backend
py -3.11 -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

### 3. Instalar Tesseract OCR

Verificar instalación:

```
tesseract --version
```

---

### 4. Descargar modelo de lenguaje

```
python -m spacy download es_core_news_sm
```

---

### 5. Ejecutar servidor

```
uvicorn app.main:app --reload
```

Acceder a:

```
http://127.0.0.1:8000/docs
```

---

## 🚀 Funcionalidades (en desarrollo)

* 📄 Carga de documentos
* 🔍 OCR de facturas
* 🧹 Procesamiento de texto
* 🧠 Clasificación automática

---

## ⚠️ Estado del Proyecto

🚧 En desarrollo

---

## 👨‍💻 Autor

**Kenedy Elio**
Estudiante de Ingeniería de Ciencia de Datos e IA

---

## 📄 Licencia

Este proyecto está bajo la licencia Apache License 2.0.
