import pandas as pd
import os

# Crear directorio para archivos de prueba
os.makedirs('archivos_prueba', exist_ok=True)

# 1. Archivo con letras en precios/stocks (Prueba 1 - Clientes)
datos_con_letras = pd.DataFrame({
    'Correo Electrónico': ['cliente1@test.com', 'cliente2@test.com', 'cliente3@test.com'],
    'Nombre Completo': ['Juan Pérez', 'María García', 'Carlos López'],
    'Teléfono': ['555-1234', '555-5678', '555-9012'],
    'Dirección': ['Calle 1', 'Calle 2', 'Calle 3'],
    'Saldo Pendiente Actual (Saldo Inicial)': [1000.50, 'abc', 3000.75],  # 'abc' en fila 3
    'Consumo Total 2022': [5000.25, 6000.50, 'xyz'],  # 'xyz' en fila 4
    'Consumo Total 2023': [7000.75, 8000.25, 9000.50],
    'Consumo Total 2024': [10000.00, 11000.50, 12000.75]
})
datos_con_letras.to_excel('archivos_prueba/test_letras_en_numeros.xlsx', index=False)
print("✅ Creado: archivos_prueba/test_letras_en_numeros.xlsx")

# 2. Archivo vacío (Prueba 2 - Clientes)
datos_vacios = pd.DataFrame(columns=[
    'Correo Electrónico',
    'Nombre Completo',
    'Teléfono',
    'Dirección',
    'Saldo Pendiente Actual (Saldo Inicial)',
    'Consumo Total 2022',
    'Consumo Total 2023',
    'Consumo Total 2024'
])
datos_vacios.to_excel('archivos_prueba/test_vacio.xlsx', index=False)
print("✅ Creado: archivos_prueba/test_vacio.xlsx")

# 3. Archivo con columnas movidas/faltantes (Prueba 3 - Clientes)
datos_columnas_movidas = pd.DataFrame({
    'Correo Electrónico': ['cliente1@test.com', 'cliente2@test.com'],
    'Nombre Completo': ['Juan Pérez', 'María García'],
    'Teléfono': ['555-1234', '555-5678'],
    'Dirección': ['Calle 1', 'Calle 2'],
    # Faltan: Saldo Pendiente Actual (Saldo Inicial), Consumo Total 2022
    'Consumo Total 2023': [7000.75, 8000.25],
    'Consumo Total 2024': [10000.00, 11000.50]
})
datos_columnas_movidas.to_excel('archivos_prueba/test_columnas_faltantes.xlsx', index=False)
print("✅ Creado: archivos_prueba/test_columnas_faltantes.xlsx")

# 4. Archivo válido (Prueba 4 - Clientes)
datos_validos = pd.DataFrame({
    'Correo Electrónico': ['cliente1@test.com', 'cliente2@test.com', 'cliente3@test.com'],
    'Nombre Completo': ['Juan Pérez', 'María García', 'Carlos López'],
    'Teléfono': ['555-1234', '555-5678', '555-9012'],
    'Dirección': ['Calle 1', 'Calle 2', 'Calle 3'],
    'Saldo Pendiente Actual (Saldo Inicial)': [1000.50, 2000.75, 3000.00],
    'Consumo Total 2022': [5000.25, 6000.50, 7000.75],
    'Consumo Total 2023': [8000.00, 9000.25, 10000.50],
    'Consumo Total 2024': [11000.75, 12000.00, 13000.25]
})
datos_validos.to_excel('archivos_prueba/test_valido.xlsx', index=False)
print("✅ Creado: archivos_prueba/test_valido.xlsx")

# 5. Archivo con letras en precios/stocks (Prueba 1 - Productos)
datos_productos_letras = pd.DataFrame({
    'Nombre del Producto': ['Producto A', 'Producto B', 'Producto C'],
    'Categoría': ['Herramientas', 'Electrónicos', 'Oficina'],
    'Unidad de Medida': ['Pieza', 'Pieza', 'Pieza'],
    'Marca': ['Marca A', 'Marca B', 'Marca C'],
    'Proveedor': ['Proveedor A', 'Proveedor B', 'Proveedor C'],
    'Costo de Compra ($)': [50.0, 'abc', 100.0],  # 'abc' en fila 3
    'Precio Menudeo ($)': [100.0, 150.0, 'xyz'],  # 'xyz' en fila 4
    'Precio Mayoreo ($)': [80.0, 120.0, 160.0],
    'Cantidad Mínima para Mayoreo': [12, 24, 36],
    'Inventario Inicial (Stock Actual)': [10, 20, 'def'],  # 'def' en fila 5
    'Inventario Mínimo de Alerta': [5, 10, 15],
    'Estatus (Activo/Inactivo)': ['Activo', 'Activo', 'Activo'],
    'Descripción técnica': ['Desc A', 'Desc B', 'Desc C']
})
datos_productos_letras.to_excel('archivos_prueba/test_productos_letras.xlsx', index=False)
print("✅ Creado: archivos_prueba/test_productos_letras.xlsx")

# 6. Archivo vacío (Prueba 2 - Productos)
datos_productos_vacios = pd.DataFrame(columns=[
    'Nombre del Producto',
    'Categoría',
    'Unidad de Medida',
    'Marca',
    'Proveedor',
    'Costo de Compra ($)',
    'Precio Menudeo ($)',
    'Precio Mayoreo ($)',
    'Cantidad Mínima para Mayoreo',
    'Inventario Inicial (Stock Actual)',
    'Inventario Mínimo de Alerta',
    'Estatus (Activo/Inactivo)',
    'Descripción técnica'
])
datos_productos_vacios.to_excel('archivos_prueba/test_productos_vacio.xlsx', index=False)
print("✅ Creado: archivos_prueba/test_productos_vacio.xlsx")

# 7. Archivo con columnas movidas/faltantes (Prueba 3 - Productos)
datos_productos_columnas = pd.DataFrame({
    'Nombre del Producto': ['Producto A', 'Producto B'],
    'Categoría': ['Herramientas', 'Electrónicos'],
    # Faltan: Costo de Compra ($), Precio Menudeo ($)
    'Precio Mayoreo ($)': [80.0, 120.0],
    'Cantidad Mínima para Mayoreo': [12, 24],
    'Inventario Inicial (Stock Actual)': [10, 20],
    'Inventario Mínimo de Alerta': [5, 10],
    'Estatus (Activo/Inactivo)': ['Activo', 'Activo'],
    'Descripción técnica': ['Desc A', 'Desc B']
})
datos_productos_columnas.to_excel('archivos_prueba/test_productos_columnas_faltantes.xlsx', index=False)
print("✅ Creado: archivos_prueba/test_productos_columnas_faltantes.xlsx")

# 8. Archivo válido (Prueba 4 - Productos)
datos_productos_validos = pd.DataFrame({
    'Nombre del Producto': ['Producto A', 'Producto B', 'Producto C'],
    'Categoría': ['Herramientas', 'Electrónicos', 'Oficina'],
    'Unidad de Medida': ['Pieza', 'Pieza', 'Pieza'],
    'Marca': ['Marca A', 'Marca B', 'Marca C'],
    'Proveedor': ['Proveedor A', 'Proveedor B', 'Proveedor C'],
    'Costo de Compra ($)': [50.0, 75.0, 100.0],
    'Precio Menudeo ($)': [100.0, 150.0, 200.0],
    'Precio Mayoreo ($)': [80.0, 120.0, 160.0],
    'Cantidad Mínima para Mayoreo': [12, 24, 36],
    'Inventario Inicial (Stock Actual)': [10, 20, 30],
    'Inventario Mínimo de Alerta': [5, 10, 15],
    'Estatus (Activo/Inactivo)': ['Activo', 'Activo', 'Activo'],
    'Descripción técnica': ['Desc A', 'Desc B', 'Desc C']
})
datos_productos_validos.to_excel('archivos_prueba/test_productos_valido.xlsx', index=False)
print("✅ Creado: archivos_prueba/test_productos_valido.xlsx")

print("\n📁 Archivos de prueba creados en 'archivos_prueba/'")
print("🧪 Archivos para CLIENTES:")
print("   1. test_letras_en_numeros.xlsx - Debe detectar error en fila 3 (Saldo) o fila 4 (Consumo 2022)")
print("   2. test_vacio.xlsx - Debe detectar que el archivo está vacío")
print("   3. test_columnas_faltantes.xlsx - Debe detectar columnas faltantes")
print("   4. test_valido.xlsx - Debe importar correctamente (3 clientes)")
print("\n🧪 Archivos para PRODUCTOS:")
print("   1. test_productos_letras.xlsx - Debe detectar error en fila 3 (Costo), fila 4 (Precio Menudeo) o fila 5 (Stock)")
print("   2. test_productos_vacio.xlsx - Debe detectar que el archivo está vacío")
print("   3. test_productos_columnas_faltantes.xlsx - Debe detectar columnas faltantes")
print("   4. test_productos_valido.xlsx - Debe importar correctamente (3 productos)")

