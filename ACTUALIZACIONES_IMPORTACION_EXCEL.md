# Actualizaciones del Módulo de Importación Excel

## Visión General

El módulo de importación Excel permite cargar **clientes** y **productos** de forma masiva desde archivos `.xlsx` con validación de datos en tiempo real y modo de prueba (dry-run).

---

## Importación de Clientes

### Endpoint

`POST /api/v1/customers/import`

### Parámetros

| Parámetro  | Tipo    | Default | Descripción                                          |
| ---------- | ------- | ------- | ---------------------------------------------------- |
| `file`     | File    | -       | Archivo Excel .xlsx                                  |
| `dry_run`  | boolean | `true`  | Si es `true`, solo valida sin guardar                |

### Formato esperado (columnas del Excel)

| Columna          | Tipo   | Requerido | Descripción                        |
| ---------------- | ------ | --------- | ---------------------------------- |
| `nombre`         | string | Sí        | Nombre del cliente                 |
| `email`          | string | Sí        | Correo electrónico (único)         |
| `telefono`       | string | No        | Teléfono                           |
| `direccion`      | string | No        | Dirección                          |
| `saldo_inicial`  | number | No        | Deuda histórica inicial            |

### Validaciones

-   **Duplicados por email**: Si un cliente con el mismo email ya existe, se omite o marca error
-   **Formato de email**: Debe ser un email válido
-   **Nombre requerido**: No puede estar vacío
-   **Dry-run**: En modo prueba, se muestran los errores sin afectar la BD

### Flujo

1. Usuario descarga plantilla `GET /api/v1/customers/template`
2. Llena datos en Excel
3. Sube archivo con `dry_run=true`
4. Sistema devuelve:
    - Registros válidos (vista previa)
    - Errores por fila
5. Usuario corrige errores y repite
6. Sube con `dry_run=false` para importar definitivamente

---

## Importación de Productos

### Endpoint

`POST /api/v1/products/import`

### Parámetros

| Parámetro | Tipo | Default | Descripción               |
| --------- | ---- | ------- | ------------------------- |
| `file`    | File | -       | Archivo Excel .xlsx       |

### Formato esperado (columnas del Excel)

| Columna             | Tipo   | Requerido | Descripción                         |
| ------------------- | ------ | --------- | ----------------------------------- |
| `nombre`            | string | Sí        | Nombre del producto                 |
| `descripcion`       | string | No        | Descripción                         |
| `marca`             | string | No        | Marca del producto                  |
| `categoria`         | string | No        | Categoría                           |
| `proveedor`         | string | No        | Nombre del proveedor                |
| `costo`             | number | Sí        | Costo del producto                  |
| `precio_menudeo`    | number | Sí        | Precio al menudeo                   |
| `precio_mayoreo`    | number | No        | Precio al mayoreo                   |
| `cantidad_mayoreo`  | number | No        | Cantidad mínima para precio mayoreo |
| `stock`             | number | No        | Stock actual (default 0)            |
| `stock_minimo`      | number | No        | Stock mínimo para alertas           |
| `unidad_medida`     | string | No        | Unidad de medida (pieza, kg, etc.)  |
| `activo`            | boolean| No        | Producto activo (default true)      |

### Validaciones

-   **Nombre requerido**: No puede estar vacío
-   **Costo y precio_menudeo**: Deben ser números mayores a 0
-   **Stock**: Debe ser número entero >= 0
-   **Duplicados**: Se detectan por nombre (case-insensitive)

---

## Exportación a Excel

### Clientes

`GET /api/v1/customers/export`

Descarga un archivo Excel con todos los clientes registrados.

### Productos

`GET /api/v1/products/export`

Descarga un archivo Excel con todo el catálogo de productos.

---

## Plantillas Descargables

### Clientes

`GET /api/v1/customers/template`

Descarga un archivo Excel con los encabezados correctos y una fila de ejemplo.

### Productos

`GET /api/v1/products/template`

Descarga un archivo Excel con los encabezados correctos y una fila de ejemplo.

---

## Historial de Cambios

### Versión 1.0 (Inicial)

-   Importación básica de clientes con validación de email
-   Importación básica de productos
-   Exportación a Excel
-   Plantillas descargables

### Mejoras Implementadas

-   **Dry-run mode**: Vista previa antes de importar
-   **Validación mejorada**: Detección de duplicados, formato de datos
-   **Manejo de errores**: Reporte detallado de errores por fila
-   **Revertibilidad**: Las importaciones fallidas no afectan la BD
-   **Soporte para marcas**: Campo `marca` agregado a productos

---

## Notas Técnicas

-   Los archivos Excel deben ser `.xlsx` (no soporta `.xls`)
-   Tamaño máximo de archivo: determinado por la configuración de FastAPI (default 5 MB)
-   La codificación debe ser UTF-8
-   Los encabezados deben coincidir exactamente con los nombres de columna documentados
-   Las filas con errores se reportan individualmente, las filas válidas se importan
