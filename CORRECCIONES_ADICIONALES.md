# Correcciones Adicionales para Portabilidad

## Fecha: 25 de Mayo de 2026

## Problema Reportado
En la otra computadora, el servidor inicia pero hay errores 500 al cargar el dashboard y los clientes activos. La documentación de la API carga correctamente.

## Causas Identificadas

### 1. Dependencia faltante: fpdf2
**Problema**: El archivo `app/api/v1/endpoints/dashboard.py` usa `from fpdf import FPDF` pero la dependencia no estaba en requirements.txt.

**Solución**: Agregado `fpdf2>=2.7.0` a requirements.txt

### 2. Ruta relativa en payments.py
**Problema**: El archivo `app/api/v1/endpoints/payments.py` usaba `templates = Jinja2Templates(directory="app/templates")` con ruta relativa.

**Solución**: Corregido para usar ruta absoluta con BASE_DIR

## Archivos Modificados

1. **requirements.txt**
   - Agregado: `fpdf2>=2.7.0`

2. **app/api/v1/endpoints/payments.py**
   - Agregado: `import os`
   - Agregado: `BASE_DIR` calculation
   - Corregido: `templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))`

## Instrucciones para Actualizar

### En la computadora original (donde hice los cambios):

```bash
# 1. Ver el estado de los cambios
git status

# 2. Agregar los archivos modificados
git add requirements.txt
git add app/api/v1/endpoints/payments.py
git add CORRECCIONES_ADICIONALES.md

# 3. Hacer commit
git commit -m "Corregir errores 500 en dashboard y clientes activos

- Agregar dependencia fpdf2 faltante a requirements.txt
- Corregir ruta relativa de templates en payments.py
- Usar rutas absolutas para portabilidad"

# 4. Push al repositorio
git push origin master
```

### En la otra computadora:

```bash
# 1. Descargar los cambios
git pull origin master

# 2. Instalar la nueva dependencia
pip install fpdf2>=2.7.0

# 3. Reiniciar el servidor
uvicorn app.main:app --reload
```

## Verificación

Después de aplicar estas correcciones, verificar:
1. El dashboard carga correctamente sin errores 500
2. La lista de clientes activos carga correctamente
3. Los reportes PDF se generan correctamente
