import pandas as pd

data = [
    {
        'Nombre Completo': 'Cliente Prueba 1',
        'Correo Electrónico': 'cliente1@ejemplo.com',
        'Teléfono': '555-1001',
        'Dirección': 'Av Siempre Viva 1',
        'Saldo Pendiente Actual (Saldo Inicial)': 0,
        'Consumo Total 2022': 1000,
        'Consumo Total 2023': 2000,
        'Consumo Total 2024': 3000,
        'Consumo Total 2025': 4000,
        'Consumo Total 2026': 5000
    },
    {
        'Nombre Completo': 'Cliente Prueba 2',
        'Correo Electrónico': 'cliente2@ejemplo.com',
        'Teléfono': '555-1002',
        'Dirección': 'Av Siempre Viva 2',
        'Saldo Pendiente Actual (Saldo Inicial)': 150.50,
        'Consumo Total 2022': 500,
        'Consumo Total 2023': 600,
        'Consumo Total 2024': 700,
        'Consumo Total 2025': 800,
        'Consumo Total 2026': 900
    },
    {
        'Nombre Completo': 'Cliente Prueba 3',
        'Correo Electrónico': 'cliente3@ejemplo.com',
        'Teléfono': '555-1003',
        'Dirección': 'Av Siempre Viva 3',
        'Saldo Pendiente Actual (Saldo Inicial)': 0,
        'Consumo Total 2022': 0,
        'Consumo Total 2023': 0,
        'Consumo Total 2024': 100,
        'Consumo Total 2025': 200,
        'Consumo Total 2026': 300
    }
]

df = pd.DataFrame(data)
df.to_excel('clientes_para_importar.xlsx', index=False, engine='openpyxl')
print('Archivo clientes_para_importar.xlsx generado con éxito.')
