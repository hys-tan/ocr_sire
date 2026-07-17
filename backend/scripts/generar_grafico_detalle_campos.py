import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Datos actualizados de PaddleOCR Puro (con la moneda corregida)
data = {
    'Campo': [
        'comprobante_serie',
        'comprobante_numero',
        'comprobante_moneda',
        'comprobante_fecha',
        'receptor_ruc_dni',
        'emisor_ruc',
        'emisor_razon_social',
        'montos_igv',
        'montos_total',
        'montos_subtotal',
        'comprobante_tipo',
        'receptor_razon_social'
    ],
    'Precisión': [
        98.02, 98.02, 97.03, 96.04, 86.14, 77.23, 57.43, 42.57, 34.65, 19.80, 11.88, 1.98
    ]
}

df = pd.DataFrame(data)

# Ordenar de mayor a menor para el gráfico de barras horizontales
df = df.sort_values(by='Precisión', ascending=True)

# Asignar colores basados en los umbrales de la imagen
def get_color(val):
    if val >= 75:
        return '#307C3B' # Verde
    elif val >= 30:
        return '#F5A623' # Naranja/Amarillo
    else:
        return '#C82A27' # Rojo

colors = [get_color(val) for val in df['Precisión']]

# Crear la figura
plt.figure(figsize=(10, 6))
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'serif'

# Dibujar las barras (horizontales)
bars = plt.barh(df['Campo'], df['Precisión'], color=colors, edgecolor='none')

# Añadir etiquetas de datos
for bar in bars:
    width = bar.get_width()
    label_x_pos = width + 1
    plt.text(label_x_pos, bar.get_y() + bar.get_height()/2, f'{width:.2f}', 
             va='center', ha='left', fontsize=9, color='black', fontfamily='serif')

# Formatear el gráfico
plt.xlabel('Precisión de extracción exacta (%)', fontsize=12, fontfamily='serif')
plt.xlim(0, 105) # Dejar espacio para las etiquetas a la derecha

# Ocultar bordes innecesarios
ax = plt.gca()
ax.spines['top'].set_visible(True)
ax.spines['right'].set_visible(True)
ax.spines['bottom'].set_visible(True)
ax.spines['left'].set_visible(True)
ax.xaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
ax.yaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)

plt.tight_layout()

# Guardar la imagen
output_path = os.path.join(os.path.dirname(__file__), '..', 'test', 'reportes', 'precision_campos_actualizado.png')
plt.savefig(output_path, dpi=300)
print(f"Gráfico actualizado generado en: {output_path}")
