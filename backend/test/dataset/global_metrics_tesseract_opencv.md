# Reporte de Métricas: Tesseract + OpenCV

- **Motor:** Tesseract con preprocesamiento en OpenCV
- **Facturas evaluadas:** 101
- **Total de campos evaluados:** 1212
- **Total de aciertos exactos:** 254
- **Precisión Global:** `20.96%`

## Precisión por Calidad del Documento
- **Calidad 'baja':** `10.17%` (50 facturas)
- **Calidad 'alta':** `31.54%` (51 facturas)

## Precisión por Campo de Datos (Matriz Cruzada)
| Campo de Dato | Global | Calidad 'alta' | Calidad 'baja' |
|:---|:---|:---|:---|
| **comprobante_tipo** | `11.88%` | `1.96%` | `22.00%` |
| **comprobante_serie** | `37.62%` | `64.71%` | `10.00%` |
| **comprobante_numero** | `45.54%` | `78.43%` | `12.00%` |
| **comprobante_fecha_emision** | `56.44%` | `92.16%` | `20.00%` |
| **comprobante_moneda** | `0.00%` | `0.00%` | `0.00%` |
| **emisor_ruc** | `11.88%` | `3.92%` | `20.00%` |
| **emisor_razon_social** | `2.97%` | `1.96%` | `4.00%` |
| **receptor_ruc_dni** | `48.51%` | `84.31%` | `12.00%` |
| **receptor_razon_social** | `9.90%` | `17.65%` | `2.00%` |
| **montos_subtotal** | `8.91%` | `7.84%` | `10.00%` |
| **montos_igv** | `11.88%` | `15.69%` | `8.00%` |
| **montos_total** | `5.94%` | `9.80%` | `2.00%` |

Los detalles por factura están guardados en: `metrics_tesseract_opencv.csv`
