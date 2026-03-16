# RBSoftware — PROJECT_CONTEXT.md

## 1. Qué es RBSoftware

RBSoftware es la **plataforma central de operación** de RobotSchool. Es un monolito modular que centraliza y digitaliza los procesos operativos, comerciales, académicos y administrativos del negocio.

No es solo una tienda, ni solo un ERP, ni solo un sistema académico. Es una plataforma que conecta múltiples capas del negocio:

- Ventas (WooCommerce, POS, manual)
- Producción de kits
- Fulfillment y logística
- Inventario de kits y componentes
- Operación interna de bodega
- Gestión académica (Escuela interna + convenios con colegios)
- Interacción con clientes y colegios
- Procesos administrativos y financieros

---

## 2. El negocio: RobotSchool

RobotSchool es una empresa que:

1. **Vende kits de robótica** — cajas con componentes electrónicos, chasis MDF cortados con láser y tornillería, dirigidos a estudiantes de colegios y al público general.
2. **Dicta clases de robótica y programación** — en sus propias sedes (Escuela) y en colegios con los que tiene convenio.
3. **Asesora y capacita docentes** — en colegios aliados.
4. **Opera ferias presenciales** — stands en colegios o eventos donde se venden kits en persona.

### Sedes actuales
- 3 sedes físicas (escuelas donde se dictan clases y se puede recoger stock)
- Convenios en colegios a nivel nacional (principalmente Cundinamarca)
- Producción centralizada en sede principal Bogotá

---

## 3. El kit: producto central

Un kit es el producto central del negocio. Es una caja con componentes para armar robots, personalizada por colegio, grado y curso.

### Tipos de kit
- **Estándar / genérico** — se vende en tienda a cualquier persona
- **Personalizado por colegio** — diseñado para un colegio, grado o curso específico

### Contenido de un kit

Todo kit tiene siempre:
- **Caja** en uno de tres tamaños: S (sanduchera), L (intermedia), XL (grande)
- **Sticker de portada** — varía por kit/curso (ej. "1ro", "Kit Explorer")
- **Papelito de agradecimiento** — genérico
- **Tirilla de contenido** — específica por kit: nombre del colegio, grado, foto + nombre + cantidad de cada componente

El contenido interno del kit puede incluir:
1. **Componentes electrónicos** — batería, LEDs, ruedas, módulo LCD, etc. Se hace picking individual
2. **Chasis / corte láser** — estructura MDF del robot, producción interna. Se trata como componente en BOM para efectos de picking, pero tiene una biblioteca de archivos de corte en el sistema
3. **Tornillería** — picking de piezas pequeñas (tornillos, tuercas) empacadas en bolsitas. Deben armarse en lotes anticipados para evitar cuellos de botella

No todos los kits traen chasis ni tornillería, pero casi todos sí.

---

## 4. Canales de venta

### WooCommerce (web)
- Canal principal de ventas online
- Los pedidos llegan como órdenes de compra
- Pago vía Wompi (integra PSE, tarjetas, etc.)
- Los pedidos pueden ser de: entrega a domicilio, entrega en sede, entrega en colegio

### POS / Feria
- Venta presencial en ferias (stand en colegio o evento)
- Se requiere stock anticipado de kits
- Medios de pago: efectivo, transferencia (Bancolombia, Davivienda), tarjeta
- El POS debe registrar la venta en tiempo real y generar factura

### Manual (backoffice)
- Creación de órdenes manualmente desde el sistema (ej. pedidos masivos a colegios)

---

## 5. Flujo principal del negocio (MVP)

```
Orden entra (Woo / POS / manual)
    ↓
Pendiente de pago / aprobación
    ↓
Aprobada → se congela snapshot comercial
    ↓
Fulfillment evalúa stock disponible
    ↓
    ├── Hay stock libre → se reserva
    └── Falta stock → se genera necesidad de producción
                          ↓
                    Batch de producción
                    (agrupa órdenes hasta hora de corte diaria)
                          ↓
                    Producción ejecuta:
                    - Lee hoja maestra del batch
                    - Hace picking de componentes
                    - Arma kits
                    - Imprime tirillas de contenido
                    - Imprime tickets de envío
                          ↓
                    Entrega a Fulfillment
                          ↓
                    Packing (escaneo de orden)
                          ↓
                    Envío / entrega / recogida en sede
```

---

## 6. Modelo de producción

### Hora de corte diaria
- El sistema agrupa órdenes pendientes hasta una hora de corte (ej. 2 horas antes de fin de jornada)
- Genera automáticamente un batch de producción con las órdenes del período
- El administrador puede intervenir manualmente: agregar órdenes urgentes, retener órdenes, reordenar prioridades

### Batches de producción
Un batch puede ser de tipo:
- `SALES` — ligado a órdenes de venta específicas
- `STOCK` — producción anticipada para inventario libre
- `FAIR` — producción anticipada reservada para una feria específica
- `MANUAL` — creado manualmente por el administrador

### Filosofía de producción
- Se produce **solo lo faltante**, no el total de la orden
- Si hay stock disponible, se reserva directamente sin producir
- Los batches consolidan múltiples órdenes para optimizar el uso de recursos

### Documentos que genera el sistema para producción
1. **Hoja maestra del batch** — instrucciones globales: qué kits armar, cantidades totales, prioridades
2. **Tirillas de contenido** — generadas y optimizadas para aprovechar la hoja (múltiples tirillas por página, sin desperdicio)
3. **Tickets de envío** — uno por orden de compra, para pegar en el embalaje

---

## 7. Optimización de envíos

- Si múltiples órdenes van a la misma dirección → se consolidan en un solo envío
- Si un colegio tiene pedidos masivos con fecha de entrega acordada → se hace un único envío al colegio en esa fecha
- El administrador puede agrupar órdenes de papás que compraron en diferentes fechas pero cuyo destino es el mismo colegio

---

## 8. Inventario

### Inventario de kits terminados
Agregado por: producto + ubicación + estado

Estados posibles:
- `FREE` — disponible para cualquier orden
- `RESERVED_WEB` — reservado para orden de venta web
- `RESERVED_FAIR` — reservado para feria específica
- `PACKED` — empacado
- `SHIPPED` — enviado
- `DELIVERED` — entregado
- `TO_DISASSEMBLE` — para desarmar
- `LOST` / `DAMAGED` / `BLOCKED`

### Inventario de componentes
Agregado por: componente + ubicación + estado

Estados:
- `AVAILABLE`
- `BLOCKED`
- `DAMAGED`
- `RESERVED`

### Ubicaciones de stock
- Bodega principal
- Sedes (3 actualmente)
- Ferias (temporales)
- Colegios (para entregas masivas)

---

## 9. Colegios como entidad central

Un colegio no es solo una dirección de envío. Es una entidad con:
- Contrato o convenio con RobotSchool
- Kits personalizados por grado/curso
- Fecha(s) de entrega acordadas
- Posibles pedidos masivos (los papás compran individualmente pero la entrega es al colegio)
- Opcionalmente: clases extracurriculares dictadas por RobotSchool (asistencia, docentes)
- Opcionalmente: plataforma LMS para sus docentes y estudiantes

---

## 10. Proveedores y costos

- Proveedor principal: China (componentes electrónicos, tiempos largos, precio bajo)
- Proveedor de urgencia: local (precio alto, tiempos cortos)
- Objetivo: tener módulo de proveedores con catálogo, precios y comparación
- Calcular costo por kit en función del precio de compra real de cada componente
- Historial de precios (variación dólar, fechas de compra)

---

## 11. Facturación

- RobotSchool ya factura electrónicamente ante la DIAN
- La factura se genera en un sistema externo (no en RBSoftware en el MVP)
- RBSoftware recopila todos los datos necesarios para la factura y los expone de forma clara al área financiera
- El área financiera genera la factura en el sistema externo consultando RBSoftware

---

## 12. Usuarios del sistema

Todos los usuarios están en la tabla `users`. Las tablas de perfil extendido se agregan por tipo de actor cuando sea necesario.

### Usuarios internos (MVP)
- **Operativos** — bodega, producción, packing, envíos
- **Administrativos** — coordinadores, gestión interna, reportes
- **Comerciales** — ventas, POS, backoffice
- **Académicos** — docentes, coordinadores académicos

### Usuarios externos (fase futura)
- Clientes, padres de familia, colegios
- Tendrán login con acceso restringido a su propia información

### Campos base de usuario
- `id`, `public_id`
- `email`, `password_hash`
- `first_name`, `last_name`
- `phone`
- `position` (cargo)
- `is_active`
- `timestamps`

---

## 13. Fases de construcción

### MVP — Núcleo operativo
Lo que genera ingresos y resuelve el caos operativo inmediato:
- Auth + RBAC + Audit
- Catálogo (productos, kits, BOM, chasis + biblioteca de archivos de corte)
- Comercial (WooCommerce + manual + aprobación + snapshot)
- Inventario (kits terminados + componentes)
- Producción (batches, hora de corte, hoja maestra, tirillas, tickets)
- Fulfillment (packing, escaneo QR, envío)
- POS básico para feria

### Fase 2 — Comercial avanzado
- Proveedores (catálogo, precios, órdenes de compra)
- Costos por kit y márgenes
- Optimización avanzada de envíos
- Colegios como entidad completa (contratos, fechas, entregas masivas)
- Integración Wompi avanzada

### Fase 3 — Académico
- **Escuela interna**: cursos, estudiantes inscritos, asistencia, mensualidades, docentes, horarios
- **Colegios / LMS**: plataforma para colegios externos (material, tareas, asistencia extracurricular)

---

## 14. Lo que RBSoftware resuelve

| Problema actual | Solución en RBSoftware |
|---|---|
| Sin inventario de componentes | Módulo de inventario con movimientos y estados |
| Producción sin trazabilidad | Batches con hoja maestra y estados en tiempo real |
| Dobles fletes por falta de visibilidad | Consolidación automática de envíos por dirección |
| Tirillas impresas con desperdicio | Generación optimizada por el sistema |
| Stock para ferias sin planificación | Batches tipo FAIR con reserva anticipada |
| Ventas en feria en talonario | POS con registro en tiempo real |
| Sin control de quién hizo qué | Auditoría desde día uno |
| Órdenes de Woo sin trazabilidad interna | Snapshot congelado al aprobar + flujo completo |