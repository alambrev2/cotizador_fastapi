# Guía Sencilla: ¿Cómo funciona tu Sistema de Cotizaciones?

¡Hola! En esta guía te explicamos de manera súper sencilla, amigable y **sin palabras difíciles (tecnicismos)** de qué trata este programa, qué problemas te resuelve en el día a día y cómo fluye la información.

También hemos incluido imágenes hermosas que muestran cómo se conectan los datos entre sí.

---

## 1. ¿Qué es este programa y para qué sirve?

Imagínate que tienes un negocio donde vendes productos y realizas proyectos a la medida para tus clientes. Este programa es tu **asistente administrativo inteligente**. Te ayuda a:
1.  **Hacer presupuestos (cotizaciones)** rápido, calculando precios, descuentos e impuestos de forma automática.
2.  **No vender lo que no tienes:** El sistema sabe exactamente cuántas piezas tienes en bodega (stock) y descuenta los productos automáticamente cuando el cliente acepta un presupuesto.
3.  **Llevar cuentas claras:** Te dice exactamente cuánto dinero te debe cada cliente sumando sus compras y restando cada abono que hace.
4.  **Hacer recibos de cobro (Notas de Remisión):** Agrupa servicios especiales (como fletes o instalaciones) en una nota bonita en formato PDF lista para entregar.

---

## 2. Mapa Visual del Programa (Modelo Lógico y Funcionalidades)

Para entender cómo fluyen los procesos en la aplicación, aquí tienes una infografía interactiva que representa gráficamente las principales funcionalidades del sistema:

![Modelo Lógico y Funcionalidades de la Aplicación](temp/modelo_logico.png)

---

## 3. ¿Cómo funciona cada sección? (En palabras sencillas)

### 👥 A. Tus Clientes (El centro de tu negocio)
*   **Historial de Compras:** El programa recuerda cuánto te compró cada cliente en años pasados (2022, 2023, 2024).
*   **Estado de Cuenta Dinámico:** Como una tarjeta de crédito, el sistema calcula de inmediato el saldo total que te debe un cliente. Si te hace un abono general (sin especificar a qué compra va dirigida), el programa inteligentemente lo aplica para saldar primero sus deudas más viejas.

### 📦 B. Tus Productos (La bodega)
*   **Precio según la cantidad:** Si tu cliente te compra pocas piezas, el sistema le cobra el **precio de menudeo**. Pero si te compra muchas piezas (por ejemplo, más de 12), el sistema le aplica el **precio de mayoreo** en automático.
*   **Control de Stock:** Cuando diseñas una cotización para un cliente, el stock de tu bodega no cambia. Pero en cuanto el cliente dice **"¡Trato hecho!"** (Estado Aceptada), el sistema va corriendo virtualmente a la bodega y descuenta las piezas vendidas para que no se las ofrezcas por error a otra persona.

### 📄 C. Las Cotizaciones y sus Versiones (El historial)
*   **No se borra nada:** Si un cliente te pide hacer cambios a un presupuesto que ya le habías mandado, el programa **no borra el anterior**. En su lugar, guarda el original como histórico (llamado "Sustituido") y crea uno nuevo versión 2 (ejemplo: `C20260001-V2`). Así tienes el historial completo de cómo fue cambiando el precio.
*   **Impuestos automáticos:** Si el cliente te pide factura, el sistema le suma el 16% de IVA automáticamente. Si no, lo deja sin IVA.
*   **Financiamiento Flexible:** Puedes acordar pagos semanales. El sistema tiene una alerta de seguridad: si intentas registrar un pago semanal de menos de $600 o más de $800, te avisará que ese monto no es viable para mantener las finanzas sanas.

### 🛠️ D. Servicios y Notas de Remisión
*   A veces haces trabajos que no son productos físicos (por ejemplo: instalar, reparar o transportar). Estos se registran como **Cargos Directos**.
*   Si le hiciste 3 servicios diferentes a un cliente en el mes, puedes seleccionarlos todos juntos y el sistema generará una **Nota de Remisión en PDF** con un folio formal (como `N20260001`), lista para que tu cliente te la firme y te pague.

---

## 4. ¿Cómo se relacionan los datos? (Relación de Tablas)

En tu base de datos (donde se guarda toda la información), las cosas no están sueltas. Todo está perfectamente interconectado. Aquí tienes la representación visual de cómo se enlazan tus datos (Clientes, Cotizaciones, Productos, Pagos y Cargos):

![Relación de las Tablas en la Base de Datos](temp/relacion_tablas.png)

### Explicación simple del diagrama de relaciones:
*   Un **Cliente** puede tener **muchas Cotizaciones**, realizar **muchos Pagos** y acumular **muchos Cargos extraordinarios**.
*   Una **Cotización** tiene **muchas Productos individuales** (detallados en una lista de artículos) y puede recibir **muchos Pagos** para ir saldando su costo.
*   Una **Cotización** puede tener un "papá" (la cotización anterior), lo que permite crear las versiones (`V2`, `V3`, etc.).
*   Un **Pago** puede ir dirigido directamente a saldar una cotización específica, un cargo de servicio individual, o ser un abono global para la cuenta del cliente.
