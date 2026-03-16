# RBSoftware — AGENTS.md
# Reglas para agentes de IA

Lee este archivo completo antes de tocar cualquier código.

---

## Stack fijo

```
Backend:      FastAPI (Python) + SQLModel + Alembic
DB:           MySQL 8 (driver: PyMySQL)
Frontend:     Next.js + React + TypeScript
UI:           Tailwind CSS + shadcn/ui
Formularios:  React Hook Form
Estado:       Context + Zustand
Storage:      MinIO (S3 compatible)
Infra:        Docker + Docker Compose + Nginx
API:          REST + OpenAPI
Auth:         JWT access + refresh tokens en httpOnly cookies
```

No cambies el stack. No propongas SQLite, no propongas microservicios, no propongas ORMs alternativos.

---

## Layout del monorepo

```
/backend        FastAPI app
/frontend       Next.js app
/infra          nginx configs
compose.dev.yml
compose.prod.yml
db.sql          modelo de datos completo (DBML) — fuente de verdad
```

---

## Arquitectura: monolito modular por dominio

```
backend/app/
  core/           config, database, security
  api/            router principal + health
  domains/
    auth/
    rbac/
    audit/
    catalog/
    commercial/
    inventory/
    production/
    fulfillment/
    integrations/
```

Cada dominio tiene exactamente estas capas:
```
{domain}/
  models/       SQLModel table definitions
  schemas/      Pydantic schemas (Create / Read / Update)
  repositories/ persistencia — CRUD y queries
  services/     lógica de negocio
  routes/       FastAPI routers — delgados, sin lógica
```

---

## Estado actual del código

| Dominio | Estado |
|---|---|
| auth | modelos ✅ schemas ✅ repos ✅ servicios ✅ rutas ❌ |
| rbac | modelos ✅ schemas ✅ repos ✅ servicios ❌ rutas ❌ |
| audit | scaffold vacío |
| catalog | scaffold vacío |
| commercial | scaffold vacío |
| inventory | scaffold vacío |
| production | scaffold vacío |
| fulfillment | scaffold vacío |
| integrations | scaffold vacío |
| frontend | scaffold estático, sin conexión al backend |

Único endpoint funcional: `GET /health`

Base de datos: 6 tablas migradas (auth + rbac). Las otras 16 están definidas en `db.sql` pero sin migración.

---

## Orden de implementación

Sigue este orden. No saltes dominios.

```
1. auth          → endpoints: POST /auth/login, POST /auth/logout,
                              POST /auth/refresh, GET /auth/me
2. rbac          → servicios + endpoints CRUD de roles, permisos,
                              asignación usuario-rol
3. audit         → implementación completa
4. catalog       → productos, kits, BOM, chasis
5. commercial    → órdenes, aprobación, snapshot
6. inventory     → balances y movimientos
7. production    → batches, hora de corte
8. fulfillment   → packing, QR, cierre
9. integrations  → WooCommerce, Wompi
10. frontend     → sobre servicios ya estables
```

---

## Modelo de negocio que debes entender

### El producto central: kits

Un kit es una caja con componentes para armar robots. Tiene BOM (lista de materiales) compuesta por:
- Componentes electrónicos (picking individual)
- Chasis MDF cortado con láser (tratado como componente en BOM, pero tiene biblioteca de archivos de corte en catalog)
- Tornillería en bolsitas (se arma en lotes anticipados)

### Catálogo
- `Product` con tipos `KIT` y `COMPONENT`
- Un kit tiene `kit_bom_items` que listan sus componentes
- El chasis es un componente en BOM + tiene archivos de corte asociados (no serializar a nivel de unidad)

### Comercial
- `SalesOrder` es la fuente comercial interna después de aprobación
- Orígenes: `WOO`, `POS`, `MANUAL`
- Mientras está `PENDING` o `UNPAID`, el origen externo puede modificarla
- Al aprobar (`APPROVED`):
  - Se congela el snapshot de la orden
  - Se crean registros de fulfillment
  - Se evalúa stock disponible
  - Se reserva lo disponible
  - Se genera necesidad de producción solo para lo faltante

### Inventario
- Inventario **agregado** por producto + ubicación + estado
- No hay serialización por unidad individual
- Reservar = mover unidades de `FREE` → `RESERVED_WEB` o `RESERVED_FAIR`
- Tablas separadas para kits terminados y componentes

Estados de inventario de kits:
`FREE`, `RESERVED_WEB`, `RESERVED_FAIR`, `PACKED`, `SHIPPED`, `DELIVERED`, `TO_DISASSEMBLE`, `LOST`, `DAMAGED`, `BLOCKED`

Estados de inventario de componentes:
`AVAILABLE`, `BLOCKED`, `DAMAGED`, `RESERVED`

### Producción
- Unidad operativa central: `ProductionBatch`
- Tipos: `SALES`, `STOCK`, `FAIR`, `MANUAL`
- Se produce **solo lo faltante**, no el total
- Hora de corte diaria: el sistema agrupa órdenes pendientes y genera batch automáticamente
- El administrador puede intervenir: agregar órdenes urgentes, retener, reordenar
- `production_batch_items` incluye: `required_qty_total`, `available_stock_qty`, `to_produce_qty`

### Fulfillment
- Packing flow por orden de venta
- QR de orden: token opaco, abre contexto operativo
- QR de kit: confirma que el kit correcto entra en el packing
- Componentes sueltos: confirmación manual por cantidad
- Cierre de packing: cambia `fulfillment_status` a `PACKED`

### Integrations
- WooCommerce: webhooks + sync incremental + cron fallback
- Wompi: confirmación de pagos
- `integration_sync_state`: estado de última sincronización por integración

---

## Reglas de implementación

### Rutas
```python
# ✅ Correcto — ruta delgada
@router.post("/login")
async def login(data: LoginRequest, service: AuthService = Depends(get_auth_service)):
    return await service.authenticate(data)

# ❌ Incorrecto — lógica en la ruta
@router.post("/login")
async def login(data: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == data.email)).first()
    # ... lógica directamente aquí
```

### Repositorios
```python
# ✅ Correcto — persistencia en repositorio
class UserRepository:
    async def get_by_email(self, email: str) -> User | None:
        ...

# ❌ Incorrecto — SQL en servicio
class UserService:
    async def authenticate(self, email: str):
        user = self.session.exec(select(User).where(...))  # MAL
```

### Modelos
- Siempre usar `public_id` (UUID) como identificador expuesto en APIs
- Nunca exponer el `id` interno en respuestas de API
- Siempre incluir `created_at` y `updated_at`

### Migraciones
- Siempre crear migración con `alembic revision --autogenerate -m "descripcion"`
- Siempre revisar el archivo generado antes de aplicar
- Nunca modificar el schema directamente en la DB
- Pensar en MySQL 8: usar tipos compatibles, no asumir SQLite

### QR y seguridad
- QR tokens son opacos — generados aleatoriamente, sin datos sensibles embebidos
- `qr_token` en `sales_orders` es un token de lookup, no un payload
- Nunca exponer PII en tokens o QR codes

---

## Lo que NO debes hacer

- ❌ Inventar tablas o campos no definidos en `db.sql` sin justificación
- ❌ Mezclar lógica de un dominio dentro de otro
- ❌ Poner lógica de negocio en rutas
- ❌ Escribir SQL directo en servicios (usa repositorios)
- ❌ Crear microservicios
- ❌ Usar SQLite como solución real
- ❌ Cambiar el stack tecnológico
- ❌ Serializar inventario por unidad individual (es agregado)
- ❌ Generar producción por el total de la orden (solo el faltante)
- ❌ Exponer `id` interno en APIs (usa `public_id`)
- ❌ Guardar refresh tokens en texto plano (siempre SHA256 hash)

---

## Antes de modificar código

1. Lee `db.sql` para entender el modelo de datos actual
2. Lee el estado de Alembic (`alembic history`)
3. Lee los archivos del dominio específico que vas a tocar
4. Entiende qué tablas ya tienen migración y cuáles no
5. Trabaja en este orden: diseño → implementación → migración → tests

---

## Contexto de negocio completo

Ver `PROJECT_CONTEXT.md` para entender el negocio, los flujos y las fases de construcción.
Ver `db.sql` para el modelo de datos completo y actualizado.