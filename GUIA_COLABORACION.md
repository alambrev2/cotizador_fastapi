# Guía de Colaboración en GitHub - Cotizador Pro

Esta guía detalla los pasos y mejores prácticas para que tú y tu equipo colaboren en este proyecto de manera ordenada, evitando conflictos de código y de base de datos.

---

## Paso 1: Configuración en GitHub (Propietario del Proyecto)

Para que tus compañeros puedan subir cambios, debes darles permisos de colaborador en tu repositorio de GitHub:

1. Ve a tu repositorio en GitHub: `https://github.com/al222410908-ctrl/cotizador_fastapi-main` (o la URL de tu repositorio).
2. Haz clic en la pestaña **Settings** (Configuración) en la barra superior.
3. En el menú lateral izquierdo, haz clic en **Collaborators** (Colaboradores).
4. Haz clic en el botón verde **Add people** (Añadir personas).
5. Escribe el correo electrónico o el nombre de usuario de GitHub de tus compañeros y haz clic en **Add [nombre] to this repository**.
6. Tus compañeros recibirán un correo de invitación. **Deben aceptar la invitación** para poder subir (`push`) cambios.

---

## Paso 2: Configuración en la Computadora de cada Colaborador

Cada integrante del equipo debe seguir estos pasos para tener el proyecto corriendo localmente:

### 1. Clonar el repositorio
```bash
git clone https://github.com/al222410908-ctrl/cotizador_fastapi-main.git
cd cotizador_fastapi-main
```

### 2. Crear y activar el entorno virtual (venv)
```bash
# Crear entorno virtual
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en Linux/Mac
# source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Inicializar archivos del sistema
```bash
python setup.py
```
Esto creará automáticamente los archivos de configuración local `.env` y los directorios de logs, reportes y carpetas temporales.

---

## Paso 3: Flujo de Trabajo con Git (Ramas / Branches)

Para evitar que dos personas editen el mismo archivo a la vez y rompan la rama principal (`master` o `main`), se recomienda trabajar con **ramas de características** (Feature Branches):

### 1. Actualizar siempre tu repositorio local
Antes de empezar a programar cualquier cosa, asegúrate de estar en `master` y tener lo último:
```bash
git checkout master
git pull origin master
```

### 2. Crear una nueva rama para tu tarea
Dale un nombre descriptivo a la rama (ej. `feature/nueva-vista`, `bugfix/error-importacion`):
```bash
git checkout -b feature/nombre-de-tu-tarea
```

### 3. Realizar los cambios y hacer commit
Una vez que termines de programar y probar localmente:
```bash
git add .
git commit -m "Descripción clara de lo que agregaste o arreglaste"
```

### 4. Subir la rama a GitHub
```bash
git push -u origin feature/nombre-de-tu-tarea
```

### 5. Crear un Pull Request (PR) en GitHub
1. Entra a la página del repositorio en GitHub.
2. Verás un botón amarillo que dice **Compare & pull request** para la rama que acabas de subir. Haz clic ahí.
3. Escribe una descripción de tus cambios y crea el Pull Request.
4. El propietario o tus compañeros revisan el código y, si todo está correcto, hacen clic en **Merge pull request** para unir los cambios a la rama principal (`master`).
5. Tras el merge, todos vuelven a su rama `master` local y hacen `git pull` para descargar la versión final unificada.

---

## ⚠ REGLA DE ORO: Manejo de la Base de Datos SQLite (`database.db`)

Dado que la base de datos SQLite es un archivo binario único (`data/database.db`) y ahora está siendo rastreado por Git, deben seguir estas estrictas pautas para evitar conflictos que Git no pueda resolver automáticamente:

### El Problema de los Conflictos Binarios
Si el Colaborador A agrega un cliente en su PC y el Colaborador B agrega un producto en su PC al mismo tiempo, ambos habrán modificado el archivo `database.db`. Git no puede "fusionar" (merge) las líneas dentro de un archivo SQLite porque es binario. El primero que haga `push` subirá sus datos, y el segundo recibirá un error de conflicto insalvable al intentar hacer `pull` o `push`.

### Buenas Prácticas recomendadas:

1. **Comunicación Activa (Lock Humano)**:
   Si vas a realizar modificaciones a la base de datos (como agregar registros a través del sistema web que quieras guardar permanentemente en el repositorio), avisa a tu equipo: *"Voy a registrar datos en la BD, por favor no suban cambios en la BD en los próximos 10 minutos"*.
   
2. **Flujo rápido de BD**:
   Hacer cambios en la base de datos -> `git commit` inmediato -> `git push` inmediato. Cuanto más corto sea el tiempo que retengas cambios locales en la base de datos, menor será el riesgo de conflicto.
   
3. **Resolución de conflictos en `database.db`**:
   If alguna vez obtienen un conflicto en `data/database.db` al hacer `git pull`, Git les pedirá elegir cuál archivo conservar. Deberán decidir con cuál de las dos bases de datos quedarse usando:
   * Conservar la versión de GitHub (descartar cambios locales de BD):
     ```bash
     git checkout --theirs data/database.db
     git add data/database.db
     git commit -m "Resolver conflicto usando la base de datos remota"
     ```
   * Conservar tu versión local (sobrescribir la de GitHub):
     ```bash
     git checkout --ours data/database.db
     git add data/database.db
     git commit -m "Resolver conflicto usando la base de datos local"
     ```

---

## 🚀 Recomendación Profesional a Mediano Plazo: Base de Datos en la Nube

Si el equipo crece o editan datos constantemente a la vez, el flujo de compartir SQLite por Git se volverá molesto. La solución definitiva es **migrar a una base de datos centralizada en la nube** (como PostgreSQL o MySQL en Supabase, Render o AWS):

- **¿Cómo funciona?**: En lugar de guardar un archivo local `database.db`, el archivo `.env` de cada desarrollador apuntará a la misma URL de conexión remota (ej: `postgresql://usuario:password@host:port/database`).
- **Ventaja**: Ya no se sube la base de datos a Git. Todos leen y escriben sobre la misma base de datos en tiempo real, eliminando al 100% los conflictos de datos y permitiendo el trabajo simultáneo sin restricciones.
