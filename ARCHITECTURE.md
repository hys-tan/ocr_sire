# Arquitectura central del sistema: ocr_sire

Última actualización: 2026-06-14

Breve visión general (resumida, diagrama con flechas):

Cliente (web / mobile / CLI)
  └─> API Gateway / Backend (TypeScript)
        ├─> (sync) Inference Service (Python / FastAPI)
        └─> (async) Queue (Redis/RabbitMQ) -> Worker -> Inference Service

Inference Service (Python)
  ├─> Carga modelo desde Model Storage (S3 / artefactos)
  ├─> Preprocesamiento -> Modelo -> Postprocesamiento
  └─> Resultado -> Database (Postgres / Mongo)

Model Storage (S3)  <─  CI/CD / Training pipeline (Python)  

Observabilidad & Operaciones
  ├─> Logs structured -> Log store (ELK / Loki)
  └─> Metrics -> Prometheus + Grafana

Infra / Despliegue
  ├─> Docker images: api (TS), ml (Py)
  └─> Kubernetes / Cloud Run (deploy)

Contratos clave
- OpenAPI spec ↔ Types compartidos (TS) ↔ Cliente
- API: endpoints para subir imágenes, consultar jobs, obtener resultados
- Job states: PENDING → RUNNING → DONE / FAILED

Recomendaciones rápidas
- Separar orquestador (TS) y lógica ML (Py).  
- Usar colas para cargas grandes y procesamiento asíncrono.  
- Versionar modelos con metadatos (hash datos, hyperparams).  
- CI: lint, tests, build & push images, deploy.

Archivo conciso listo: `ARCHITECTURE.md` (rama: model_ml_2).