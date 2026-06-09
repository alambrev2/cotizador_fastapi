# Instrucciones Detalladas para Configurar en Otra Computadora

## Fecha: 25 de Mayo de 2026

## ℹ IMPORTANTE: Sincronización de Base de Datos

**El proyecto usa SQLite (base de datos local)**:
- La base de datos es un archivo local (`data/database.db`).
- Se ha configurado para ser rastreada por Git, por lo que **los datos (clientes, productos, cotizaciones, etc.) se transfieren automáticamente** al clonar o descargar el proyecto desde GitHub.
- Al ejecutar el programa en cualquier dispositivo, la base de datos se cargará con toda la información actual y estará lista para ser modificada.

**Para guardar o sincronizar tus cambios**, sigue las instrucciones de la sección "Sincronizar Cambios entre Computadoras" al final de este documento.

---

## Paso 1: Descargar el proyecto desde GitHub

### Opción A: Descargar como ZIP
1. Ir a: https://github.com/al222410908-ctrl/cotizador_fastapi-main
2. Hacer clic en el botón verde "Code"
3. Seleccionar "Download ZIP"
4. Descomprimir el archivo en una carpeta (ej: `C:\Users\TuUsuario\Desktop\cotizador_fastapi-main`)

### Opción B: Usar Git (recomendado)
```bash
# Abrir terminal o PowerShell
cd C:\Users\TuUsuario\Desktop
git clone https://github.com/al222410908-ctrl/cotizador_fastapi-main.git
cd cotizador_fastapi-main
```

## Paso 2: Ejecutar el script de inicialización

```bash
# Asegurarse de estar en el directorio del proyecto
cd C:\Users\TuUsuario\Desktop\cotizador_fastapi-main

# Ejecutar el script de inicialización
python setup.py
```

Este script creará automáticamente:
- ✅ Directorio `data/` para la base de datos
- ✅ Directorio `logs/` para los logs del sistema
- ✅ Directorio `temp/` para archivos temporales
- ✅ Directorio `app/static/reports/` para reportes PDF
- ✅ Archivo `.env` con configuración básica

## Paso 3: Crear entorno virtual

```bash
# Crear el entorno virtual
python -m venv venv

# Activar el entorno virtual (Windows)
venv\Scripts\activate

# Si estás en Linux/Mac:
# source venv/bin/activate
```

**Verificación**: Deberías ver `(venv)` al inicio de tu línea de comandos

## Paso 4: Instalar dependencias

```bash
# Asegurarse de estar en el directorio del proyecto con el entorno virtual activado
pip install -r requirements.txt
```

Esto instalará todas las dependencias incluyendo:
- fastapi, uvicorn
- sqlmodel
- pandas, openpyxl
- xhtml2pdf, fpdf2 (para generación de PDFs)
- y todas las demás dependencias necesarias

## Paso 5: Inicializar la base de datos

```bash
# Crear las tablas en la base de datos SQLite
python scripts/migrations/init_db.py
```

**Salida esperada**:
```
Creando base de datos y tablas...
¡Tablas creadas exitosamente!
```

## Paso 6: Verificar configuración

```bash
# Verificar que el archivo .env existe
dir .env

# Verificar que el directorio data existe
dir data

# Verificar que el directorio logs existe
dir logs
```

## Paso 7: Iniciar el servidor

```bash
# Iniciar el servidor de desarrollo limitando la recarga al directorio 'app'
uvicorn app.main:app --reload --reload-dir app
```

**Salida esperada**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## Paso 8: Verificar que funciona

1. **Abrir en el navegador**: http://127.0.0.1:8000
2. **Verificar la documentación de la API**: http://127.0.0.1:8000/docs
3. **Verificar Scalar docs**: http://127.0.0.1:8000/scalar

## Paso 9: Probar funcionalidades clave

### Dashboard
- Ir a: http://127.0.0.1:8000/dashboard
- Debería cargar sin errores 500
- No debería quedar en "Cargando..."

### Clientes
- Ir a: http://127.0.0.1:8000/customers
- Debería cargar la lista de clientes
- No debería haber errores 500

### Productos
- Ir a: http://127.0.0.1:8000/products
- Debería cargar la lista de productos

## Solución de Problemas Comunes

### Error: "ModuleNotFoundError: No module named 'fpdf'"
**Solución**:
```bash
pip install fpdf2>=2.7.0
```

### Error: "ModuleNotFoundError: No module named 'xhtml2pdf'"
**Solución**:
```bash
pip install xhtml2pdf>=0.2.5
```

### Error: "No such file or directory: 'data/database.db'"
**Solución**:
```bash
python setup.py
python scripts/migrations/init_db.py
```

### Error: "No such file or directory: 'logs/error.log'"
**Solución**:
```bash
python setup.py
```

### Error: "No such file or directory: 'app/templates'"
**Solución**: Esto indica que no estás ejecutando desde el directorio correcto.
```bash
# Asegurarte de estar en el directorio raíz del proyecto
cd C:\Users\TuUsuario\Desktop\cotizador_fastapi-main
# Verificar que estás en el lugar correcto
dir app
dir requirements.txt
```

### Error 500 en dashboard
**Verificar**:
1. Que el archivo .env existe
2. Que la base de datos está inicializada
3. Que todas las dependencias están instaladas
4. Revisar los logs en `logs/error.log`

## Actualizar el proyecto después de cambios en GitHub

Si ya tienes el proyecto configurado y hay cambios nuevos:

```bash
# 1. Detener el servidor (presionar CTRL+C en la terminal)

# 2. Descargar los cambios
git pull origin master

# 3. Si hay nuevas dependencias en requirements.txt
pip install -r requirements.txt

# 4. Si hay migraciones nuevas
python scripts/migrations/init_db.py

# 5. Reiniciar el servidor
uvicorn app.main:app --reload --reload-dir app
```

## Estructura de directorios esperada

Después de ejecutar `setup.py`, tu proyecto debería tener esta estructura:

```
cotizador_fastapi-main/
├── app/
│   ├── api/
│   ├── core/
│   ├── static/
│   │   └── reports/        (creado por setup.py)
│   ├── templates/
│   ├── database.py
│   ├── main.py
│   └── models.py
├── data/
│   └── database.db          (creado por init_db.py)
├── logs/
│   └── error.log            (creado por setup.py)
├── temp/                    (creado por setup.py)
├── scripts/
│   └── migrations/
├── .env                     (creado por setup.py)
├── .env.example
├── requirements.txt
├── setup.py
└── README.md
```

## Comandos útiles

```bash
# Ver versión de Python
python --version

# Ver paquetes instalados
pip list

# Verificar que el entorno virtual está activado
where python

# Ver logs de errores
type logs\error.log

# Ver logs del servidor (si se guardan)
type logs\uvicorn_error.log
```

## Soporte

Si encuentras errores no documentados aquí:
1. Revisar el archivo `logs/error.log` para ver detalles del error
2. Verificar que estás en el directorio correcto del proyecto
3. Asegurarte de que el entorno virtual está activado
4. Verificar que todas las dependencias están instaladas

---

## Sincronizar Cambios entre Computadoras

### ¿Cómo se transfieren los datos ahora?

El archivo de la base de datos local (`data/database.db`) ahora **está configurado en Git**. Esto significa que:
1. Al clonar o descargar el repositorio por primera vez en otra computadora, se descargará con todos los clientes, productos y cotizaciones actuales.
2. Al ejecutar la aplicación, cargará y modificará la base de datos local de inmediato.

---

### Método 1: Sincronizar usando Git (Recomendado)

Si haces cambios en una computadora y quieres verlos en la otra:

#### En la computadora donde hiciste los cambios:
1. Asegúrate de detener el servidor de FastAPI (`Ctrl + C`).
2. Guarda y sube los cambios de la base de datos a GitHub ejecutando en tu terminal:
   ```bash
   git add data/database.db
   git commit -m "Actualizar base de datos con nuevos datos"
   git push origin master
   ```

#### En la otra computadora:
1. Asegúrate de detener el servidor de FastAPI (`Ctrl + C`).
2. Descarga la base de datos actualizada desde GitHub ejecutando:
   ```bash
   git pull origin master
   ```
3. Vuelve a iniciar el servidor limitando la recarga a la carpeta 'app':
   ```bash
   uvicorn app.main:app --reload --reload-dir app
   ```

> [!WARNING]
> **Evita modificar la base de datos en ambas computadoras al mismo tiempo sin antes hacer `git pull`**. Si lo haces, Git generará un conflicto en el archivo binario `database.db` que no se podrá resolver automáticamente. Siempre haz un `git pull` antes de comenzar a trabajar en otra PC y haz `git push` al terminar.

---

### Método 2: Usar el script de backup (Si prefieres no usar Git para los datos)

#### En la computadora ORIGINAL (con los datos):
```bash
# 1. Ejecutar el script de backup
python scripts/backup_db.py

# 2. Seleccionar opción 1 (Exportar)
# Esto creará un archivo en la carpeta backups/ con fecha
# Ejemplo: backups/database_backup_20260525_143000.db

# 3. Copiar ese archivo a un USB, email, o carpeta compartida
```

#### En la computadora DESTINO:
```bash
# 1. Copiar el archivo de backup a la carpeta data/
# Por ejemplo: data/database_backup_20260525_143000.db

# 2. Ejecutar el script de backup
python scripts/backup_db.py

# 3. Seleccionar opción 2 (Importar)
# 4. Ingresar la ruta del archivo de backup
# Ejemplo: data/database_backup_20260525_143000.db

# 5. Reiniciar el servidor
uvicorn app.main:app --reload
```
