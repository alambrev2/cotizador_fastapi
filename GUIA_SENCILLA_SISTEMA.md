# GUÍA SENCILLA DEL SISTEMA - Cotizador Pro

## ¿Qué es Cotizador Pro?

Es un sistema web para gestionar cotizaciones, clientes, productos, pagos y finanzas de un negocio. Está diseñado para ser usado desde el navegador web, sin necesidad de instalar programas adicionales.

---

## Cómo Acceder

1. **Abrir el navegador** (Chrome, Edge, Firefox)
2. **Ingresar la dirección**: `http://localhost:8000`
3. **Iniciar sesión** con tu usuario y contraseña

---

## Pantalla de Login

-   Ingresa tu **nombre de usuario**
-   Ingresa tu **contraseña**
-   Haz clic en **Iniciar Sesión**

Si eres **cliente**, puedes usar un **token mágico** (enlace especial que te envía el administrador) para entrar sin contraseña.

---

## Roles de Usuario

| Rol              | ¿Qué puede hacer?                                                    |
| ---------------- | -------------------------------------------------------------------- |
| **Administrador**| Todo: clientes, productos, cotizaciones, pagos, usuarios, finanzas   |
| **Operativo**    | Cotizaciones, ver proyectos, dashboard. No puede crear usuarios.     |
| **Cliente**      | Ver su panel, estado de cuenta, aceptar/rechazar cotizaciones.       |

---

## Navegación Principal

### Menú Lateral (barra izquierda)

-   **Dashboard** - Resumen ejecutivo con métricas y alertas
-   **Clientes** - Lista, crear, editar, importar/exportar clientes
-   **Productos** - Lista, crear, editar, importar/exportar productos
-   **Cotizaciones** - Lista, crear, gestionar cotizaciones
-   **Estado de Cuenta** - Pagos, cargos, remisiones, saldos
-   **Finanzas** - Ingresos, gastos, estado de resultados
-   **Usuarios** - (Solo Admin) Gestionar usuarios del sistema

---

## Funcionalidades Básicas

### Clientes

-   **Ver lista**: Todos los clientes registrados
-   **Buscar**: Por nombre o correo
-   **Crear**: Nuevo cliente con datos de contacto y financieros
-   **Editar**: Modificar datos del cliente
-   **Importar**: Cargar varios clientes desde Excel
-   **Exportar**: Descargar lista a Excel

### Productos

-   **Ver catálogo**: Todos los productos con precios y stock
-   **Buscar**: Por nombre o marca
-   **Crear**: Nuevo producto con precios de menudeo/mayoreo
-   **Editar**: Modificar producto
-   **Importar**: Cargar productos desde Excel
-   **Exportar**: Descargar catálogo a Excel

### Cotizaciones

-   **Crear**: Seleccionar cliente, agregar productos, definir tipo de pago
-   **Tipos de pago**: Contado, 2 Pagos, Semanal
-   **Enviar**: Por correo electrónico con PDF adjunto
-   **PDF**: Descargar cotización en formato PDF profesional
-   **Estados**: Borrador, Enviada, Aprobación Solicitada, Aprobada, Pendiente, Cobranza Requerida, Rechazada, Sustituida, Finalizada, Cancelada
-   **Editar**: Modificar cotización (crea nueva versión)

### Pagos y Estado de Cuenta

-   **Registrar pago**: A una cotización, a un cargo, o abono global
-   **Métodos de pago**: Efectivo, Transferencia, Tarjeta
-   **Cargos/Servicios**: Registrar cargos a clientes
-   **Remisiones**: Generar nota de remisión con folio
-   **Estado de cuenta**: Ver histórico (compras, pagos, saldo)

### Finanzas

-   **Ingresos**: Registrar ingresos varios
-   **Gastos**: Registrar gastos operativos
-   **Dashboard financiero**: Gráfica de ingresos vs egresos
-   **Estado de resultados**: Utilidad/pérdida por mes

---

## Importación desde Excel

### Clientes

1. Descarga la plantilla (botón "Descargar Plantilla")
2. Llena los datos en Excel
3. Sube el archivo (botón "Importar")
4. El sistema valida los datos y muestra vista previa
5. Confirma la importación

### Productos

1. Descarga la plantilla
2. Llena los datos: nombre, marca, costo, precios, stock
3. Sube el archivo
4. El sistema valida y muestra vista previa
5. Confirma la importación

---

## Reportes PDF Disponibles

-   **Cotización**: PDF profesional con datos de la empresa y cliente
-   **Nota de Remisión**: PDF con folio N20260001
-   **Estado de Cuenta**: PDF con saldo inicial, movimientos y saldo final
-   **Reporte Financiero**: PDF de ingresos/egresos del mes

---

## Preguntas Frecuentes

### ¿Olvidé mi contraseña?

Solicita al administrador que genere un **token mágico** o reinicie tu contraseña.

### ¿No encuentro un cliente?

Usa la barra de búsqueda en la lista de clientes. Puedes buscar por nombre o correo.

### ¿Cómo saber si una cotización fue aceptada?

Revisa la columna "Estado" en la lista de cotizaciones. También verás notificaciones en el Dashboard.

### ¿Qué significa cada estado de cotización?

-   **Borrador**: Sin enviar al cliente
-   **Enviada**: Cliente notificado, esperando respuesta
-   **Aprobación Solicitada**: Cliente marcó aprobación, en revisión
-   **Aprobada**: Cliente aprobó, pendiente de pago
-   **Rechazada**: Cliente no aprobó
-   **Pendiente**: Aprobada con saldo pendiente de pago
-   **Cobranza Requerida**: Con saldo vencido o en gestión de cobranza
-   **Finalizada**: Pagada y cerrada
-   **Sustituida**: Reemplazada por una nueva versión
-   **Cancelada**: Anulada

### ¿Se puede editar una cotización después de enviarla?

Sí, al editarla se crea una nueva versión (ej. `C20260001-V2`) y la anterior queda marcada como "Sustituida".

### ¿Dónde se guardan los PDFs?

Los PDFs se generan y se pueden descargar directamente desde el navegador. También se guardan en la carpeta `app/static/reports/`.

### ¿Cómo importar datos desde Excel?

Usa las opciones de importación en las secciones de Clientes y Productos. Descarga primero la plantilla para ver el formato esperado.

---

## Soporte

Si encuentras algún error:

1. Revisa la consola del servidor (donde ejecutaste `uvicorn`)
2. Los errores detallados se guardan en `logs/error.log`
3. Contacta al administrador del sistema
