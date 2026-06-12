# Reporte de Métricas: PaddleOCR Base

- **Motor:** PaddleOCR puro (Sin OpenCV ni Tesseract)
- **Facturas evaluadas:** 101
- **Total de campos evaluados:** 1212
- **Total de aciertos exactos:** 630
- **Precisión Global:** `51.98%`

## Precisión por Calidad del Documento
- **Calidad 'baja':** `43.67%` (50 facturas)
- **Calidad 'alta':** `60.13%` (51 facturas)

## Precisión por Campo de Datos (Matriz Cruzada)
| Campo de Dato | Global | Calidad 'alta' | Calidad 'baja' |
|:---|:---|:---|:---|
| **comprobante_tipo** | `11.88%` | `1.96%` | `22.00%` |
| **comprobante_serie** | `98.02%` | `100.00%` | `96.00%` |
| **comprobante_numero** | `98.02%` | `100.00%` | `96.00%` |
| **comprobante_fecha_emision** | `96.04%` | `100.00%` | `92.00%` |
| **comprobante_moneda** | `0.00%` | `0.00%` | `0.00%` |
| **emisor_ruc** | `77.23%` | `100.00%` | `54.00%` |
| **emisor_razon_social** | `57.43%` | `96.08%` | `18.00%` |
| **receptor_ruc_dni** | `86.14%` | `100.00%` | `72.00%` |
| **receptor_razon_social** | `1.98%` | `0.00%` | `4.00%` |
| **montos_subtotal** | `19.80%` | `21.57%` | `18.00%` |
| **montos_igv** | `42.57%` | `56.86%` | `28.00%` |
| **montos_total** | `34.65%` | `45.10%` | `24.00%` |

Los detalles por factura están guardados en: `metrics_paddleocr_base.csv`
