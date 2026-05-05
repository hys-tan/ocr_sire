from fastapi import FastAPI

app = FastAPI(
    title="API OCR SIRE",
    description="API para procesar facturas y boletas usando OCR",
    version="1.0.0"
)

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API OCR SIRE"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "OCR SIRE Backend API"}
