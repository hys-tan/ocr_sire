from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import upload
from app.api import batch

app = FastAPI(
    title="API OCR SIRE",
    description="API para procesar facturas y boletas usando OCR",
    version="1.0.0"
)

# Configuración CORS para permitir peticiones desde React (Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción cambiar por la URL de React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enrutadores
app.include_router(upload.router, prefix="/api/v1")
app.include_router(batch.router,  prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API OCR SIRE"}

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "OCR SIRE Backend API"}
