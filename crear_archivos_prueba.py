import pandas as pd
import random

def generar_datos_prueba():
    # 1. Generar 300 Clientes
    clientes = []
    nombres_propios = ["Carlos", "Ana", "Luis", "Maria", "Jorge", "Sofia", "Pedro", "Elena", "Miguel", "Lucia", "David", "Laura", "Alejandro", "Isabel", "Fernando", "Carmen", "Ricardo", "Gabriela", "Francisco", "Adriana"]
    apellidos = ["Gomez", "Rodriguez", "Hernandez", "Martinez", "Lopez", "Gonzalez", "Perez", "Sanchez", "Ramirez", "Torres", "Flores", "Rivera", "Diaz", "Cruz", "Morales", "Ortiz", "Gutierrez", "Ruiz", "Alvarez", "Castillo"]
    dominios = ["gmail.com", "outlook.com", "yahoo.com", "empresa.mx", "negocios.com.mx"]
    calles = ["Av. Reforma", "Calle Juárez", "Av. Insurgentes", "Calle Hidalgo", "Av. Constitución", "Calle Morelos", "Calle Zaragoza", "Av. Patria", "Calle Guerrero", "Calle Madero"]

    for i in range(1, 301):
        nombre = f"{random.choice(nombres_propios)} {random.choice(apellidos)} {random.choice(apellidos)}"
        safe_name = "".join([c for c in nombre if c.isalnum()]).lower()[:15]
        email = f"{safe_name}_{i}@{random.choice(dominios)}"
        telefono = f"555{random.randint(1000000, 9999999)}"
        direccion = f"{random.choice(calles)} #{random.randint(1, 2500)}, Col. Centro, CP {random.randint(10000, 99000)}"
        saldo_inicial = round(random.choice([0.0, 0.0, 0.0, 1500.0, 3200.50, 450.0, 12000.0]), 2)
        
        # Consumos históricos
        consumo_2022 = round(random.uniform(1000, 25000), 2)
        consumo_2023 = round(random.uniform(2000, 35000), 2)
        consumo_2024 = round(random.uniform(5000, 50000), 2)
        consumo_2025 = round(random.uniform(5000, 60000), 2)
        consumo_2026 = round(random.uniform(5000, 75000), 2)
        
        clientes.append({
            "Nombre Completo": nombre,
            "Correo Electrónico": email,
            "Teléfono": telefono,
            "Dirección": direccion,
            "Saldo Pendiente Actual (Saldo Inicial)": saldo_inicial,
            "Consumo Total 2022": consumo_2022,
            "Consumo Total 2023": consumo_2023,
            "Consumo Total 2024": consumo_2024,
            "Consumo Total 2025": consumo_2025,
            "Consumo Total 2026": consumo_2026
        })

    df_clientes = pd.DataFrame(clientes)
    df_clientes.to_excel("clientes_300.xlsx", index=False, engine="openpyxl")
    print("OK: Archivo 'clientes_300.xlsx' con 300 registros generado exitosamente.")

    # 2. Generar 300 Productos
    productos = []
    categorias = ["Herramientas", "Iluminación", "Seguridad", "Material Eléctrico", "Plomería", "Pintura", "Ferretería", "Jardinería"]
    marcas = ["Truper", "Phillips", "Bticino", "3M", "Coflex", "Comex", "Rotoplas", "Stanley", "Dewalt", "Bosch"]
    nombres_herramientas = [
        "Martillo de uña", "Destornillador Phillips", "Pinzas de presión", "Llave inglesa 10''", "Flexómetro 5m",
        "Taladro percutor", "Lámpara LED 12W", "Cable eléctrico Calibre 12", "Apagador sencillo", "Contacto duplex",
        "Cinta aislante", "Tubo PVC 1/2''", "Coflex para lavabo", "Pintura vinílica blanca", "Brocha de 3''",
        "Tornillo para madera", "Clavos de acero 2''", "Candado de seguridad", "Cámara de vigilancia wifi", "Sensor de movimiento"
    ]
    proveedores = ["Distribuidora Ferretera del Centro", "Ferretera Nacional S.A.", "Materiales y Soluciones Eléctricas", "Proveedor Eléctrico del Norte"]
    unidades = ["Pieza", "Metro", "Caja", "Paquete", "Litro"]

    for i in range(1, 301):
        nombre_prod = f"{random.choice(nombres_herramientas)} {random.choice(marcas)} Mod-{random.randint(100, 999)}"
        # Evitar duplicidad exacta de nombres en el bucle
        nombre_prod = f"{nombre_prod} ({i})"
        
        categoria = random.choice(categorias)
        marca = random.choice(marcas)
        proveedor = random.choice(proveedores)
        unidad_medida = random.choice(unidades)
        
        costo = round(random.uniform(5.0, 1500.0), 2)
        precio_menudeo = round(costo * random.uniform(1.3, 1.6), 2)
        precio_mayoreo = round(costo * random.uniform(1.1, 1.25), 2)
        
        cant_mayoreo = random.choice([6, 12, 24, 50])
        stock = random.randint(10, 500)
        stock_minimo = random.randint(5, 30)
        
        productos.append({
            "Nombre del Producto": nombre_prod,
            "Categoría": categoria,
            "Unidad de Medida": unidad_medida,
            "Marca": marca,
            "Proveedor": proveedor,
            "Costo de Compra ($)": costo,
            "Precio Menudeo ($)": precio_menudeo,
            "Precio Mayoreo ($)": precio_mayoreo,
            "Cantidad Mínima para Mayoreo": cant_mayoreo,
            "Inventario Inicial (Stock Actual)": stock,
            "Inventario Mínimo de Alerta": stock_minimo,
            "Estatus (Activo/Inactivo)": "Activo",
            "Descripción técnica": f"Producto de alta calidad marca {marca}. Diseñado para uso industrial y doméstico."
        })

    df_productos = pd.DataFrame(productos)
    df_productos.to_excel("productos_300.xlsx", index=False, engine="openpyxl")
    print("OK: Archivo 'productos_300.xlsx' con 300 registros generado exitosamente.")

if __name__ == "__main__":
    generar_datos_prueba()
