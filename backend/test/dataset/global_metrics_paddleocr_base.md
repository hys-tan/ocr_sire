# Reporte de Métricas: PaddleOCR Base

- **Motor:** PaddleOCR puro (Sin OpenCV ni Tesseract)
- **Facturas evaluadas:** 101
- **Total de campos evaluados:** 1212
- **Total de aciertos exactos:** 630
- **Precisión Global:** `51.98%`

## Precisión por Calidad del Documento
- **Calidad 'baja':** `43.67%` (50 facturas)
- **Calidad 'alta':** `60.13%` (51 facturas)

## Precisión por Campo de Datos
- **comprobante_tipo:** `11.88%`
- **comprobante_serie:** `98.02%`
- **comprobante_numero:** `98.02%`
- **comprobante_fecha_emision:** `96.04%`
- **comprobante_moneda:** `0.00%`
- **emisor_ruc:** `77.23%`
- **emisor_razon_social:** `57.43%`
- **receptor_ruc_dni:** `86.14%`
- **receptor_razon_social:** `1.98%`
- **montos_subtotal:** `19.80%`
- **montos_igv:** `42.57%`
- **montos_total:** `34.65%`

Los detalles por factura están guardados en: `metrics_paddleocr_base.csv`
