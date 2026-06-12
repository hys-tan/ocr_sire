# Reporte de Métricas: Tesseract Base

- **Motor:** Tesseract puro (Sin OpenCV)
- **Facturas evaluadas:** 101
- **Total de campos evaluados:** 1212
- **Total de aciertos exactos:** 284
- **Precisión Global:** `23.43%`

## Precisión por Calidad del Documento
- **Calidad 'baja':** `11.67%` (50 facturas)
- **Calidad 'alta':** `34.97%` (51 facturas)

## Precisión por Campo de Datos (Matriz Cruzada)
| Campo de Dato | Global | Calidad 'alta' | Calidad 'baja' |
|:---|:---|:---|:---|
| **comprobante_tipo** | `9.90%` | `1.96%` | `18.00%` |
| **comprobante_serie** | `22.77%` | `29.41%` | `16.00%` |
| **comprobante_numero** | `24.75%` | `35.29%` | `14.00%` |
| **comprobante_fecha_emision** | `64.36%` | `100.00%` | `28.00%` |
| **comprobante_moneda** | `0.00%` | `0.00%` | `0.00%` |
| **emisor_ruc** | `11.88%` | `9.80%` | `14.00%` |
| **emisor_razon_social** | `1.98%` | `1.96%` | `2.00%` |
| **receptor_ruc_dni** | `58.42%` | `100.00%` | `16.00%` |
| **receptor_razon_social** | `8.91%` | `17.65%` | `0.00%` |
| **montos_subtotal** | `16.83%` | `21.57%` | `12.00%` |
| **montos_igv** | `34.65%` | `56.86%` | `12.00%` |
| **montos_total** | `26.73%` | `45.10%` | `8.00%` |

Los detalles por factura están guardados en: `metrics_tesseract_base.csv`
