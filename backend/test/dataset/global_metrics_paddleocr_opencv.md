# Reporte de Métricas: PaddleOCR + OpenCV

- **Motor:** PaddleOCR con preprocesamiento en OpenCV
- **Facturas evaluadas:** 101
- **Total de campos evaluados:** 1212
- **Total de aciertos exactos:** 493
- **Precisión Global:** `40.68%`

## Precisión por Calidad del Documento
- **Calidad 'baja':** `30.67%` (50 facturas)
- **Calidad 'alta':** `50.49%` (51 facturas)

## Precisión por Campo de Datos (Matriz Cruzada)
| Campo de Dato | Global | Calidad 'alta' | Calidad 'baja' |
|:---|:---|:---|:---|
| **comprobante_tipo** | `9.90%` | `1.96%` | `18.00%` |
| **comprobante_serie** | `83.17%` | `100.00%` | `66.00%` |
| **comprobante_numero** | `83.17%` | `100.00%` | `66.00%` |
| **comprobante_fecha_emision** | `70.30%` | `96.08%` | `44.00%` |
| **comprobante_moneda** | `0.00%` | `0.00%` | `0.00%` |
| **emisor_ruc** | `83.17%` | `100.00%` | `66.00%` |
| **emisor_razon_social** | `59.41%` | `94.12%` | `24.00%` |
| **receptor_ruc_dni** | `62.38%` | `80.39%` | `44.00%` |
| **receptor_razon_social** | `0.99%` | `0.00%` | `2.00%` |
| **montos_subtotal** | `12.87%` | `13.73%` | `12.00%` |
| **montos_igv** | `14.85%` | `15.69%` | `14.00%` |
| **montos_total** | `7.92%` | `3.92%` | `12.00%` |

Los detalles por factura están guardados en: `metrics_paddleocr_opencv.csv`
