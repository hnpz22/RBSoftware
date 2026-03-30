# RBSoftware — ARCHITECTURE.md

## 1. Tipo de arquitectura

**Monolito modular**. Todo vive en un solo proyecto, dividido claramente por dominios. No hay microservicios. Cada dominio tiene sus propias capas internas y no puede acceder directamente a las capas internas de otro dominio.

---

## 2. Stack tecnológico

### Backend
| Capa | Tecnología |
|---|---|
| Framework | FastAPI (Python) |
| ORM | SQLModel |
| Migraciones | Alembic |
| Base de datos | MySQL 8 |
| Driver MySQL | PyMySQL |
| Autenticación | JWT (HS256) access + refresh tokens |
| Hashing | bcrypt (passwords), SHA256 (refresh tokens) |
| Testing | pytest |

### Frontend
| Capa | Tecnología |
|---|---|
| Framework | Next.js (App Router) |
| Lenguaje | TypeScript |
| UI | Tailwind CSS + shadcn/ui |
| Formularios | React Hook Form |
| Estado global | Context + Zustand |

### Infraestructura
| Componente | Tecnología |
|---|---|
| Contenedores | Docker + Docker Compose |
| Proxy reverso | Nginx |
| Almacenamiento objetos | MinIO (S3 compatible) |
| Servidor objetivo | Linux / Ubuntu Server (VPS Hostinger) |

### API
- REST + OpenAPI
- Documentación automática en `/docs` (Swagger) y `/redoc`

---

## 3. Estructura del repositorio

```
RBSoftware/                   ← monorepo raíz
├── backend/                  ← FastAPI app
├── frontend/                 ← Next.js app
├── infra/                    ← nginx configs
├── compose.dev.yml           ← stack de desarrollo
├── compose.prod.yml          ← stack de producción
├── .env.example              ← variables de entorno de referencia
├── db.sql                    ← modelo de datos completo (DBML)
├── AGENTS.md                 ← reglas para agentes de IA
├── ARCHITECTURE.md           ← este archivo
└── PROJECT_CONTEXT.md        ← contexto de negocio
```

---

## 4. Estructura del backend

```
backend/
├── alembic/
│   ├── env.py
│   └── versions/             ← migraciones (una por cambio de schema)
├── app/
│   ├── main.py               ← entrada FastAPI, registro de routers
│   ├── core/
│   │   ├── config.py         ← settings (pydantic-settings)
│   │   ├── database.py       ← engine, session, get_session
│   │   ├── security.py       ← JWT, bcrypt, token utils
│   │   ├── permissions.py    ← require_roles() dependency
│   │   └── storage.py        ← MinIO storage service
│   ├── api/
│   │   ├── router.py         ← api_router principal
│   │   └── routes/
│   │       └── health.py     ← GET /health
│   └── domains/
│       ├── auth/
│       ├── rbac/
│       ├── audit/
│       ├── catalog/
│       ├── commercial/
│       ├── inventory/
│       ├── production/
│       ├── fulfillment/
│       ├── integrations/
│       └── academic/
├── tests/
├── requirements.txt
├── requirements-dev.txt
└── pyproject.toml
```

### Estructura interna de cada dominio

```
domains/{domain}/
├── models/        ← SQLModel table definitions
├── schemas/       ← Pydantic schemas (Create/Read/Update)
├── repositories/  ← persistencia (CRUD + queries específicas)
├── services/      ← lógica de negocio
└── routes/        ← FastAPI routers (delgados, sin lógica)
```

**Regla**: la lógica de negocio vive en `services/`, no en `routes/`. Las `routes/` solo validan input, llaman al servicio y retornan la respuesta.

---

## 5. Dominios del sistema

### Estado actual — todos los dominios implementados ✅

| Dominio | Modelos | Schemas | Repos | Servicios | Rutas | Migración |
|---|---|---|---|---|---|---|
| auth | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| rbac | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| audit | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| catalog | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| commercial | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| inventory | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| production | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| fulfillment | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| integrations | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| academic | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### Páginas frontend funcionales

`/login`, `/dashboard`, `/orders`, `/orders/[id]`, `/orders/new`,
`/catalog`, `/catalog/[id]`, `/inventory`, `/production`,
`/production/[id]`, `/fulfillment`, `/fulfillment/[id]`,
`/settings/users`, `/settings/roles`, `/reports`,
`/academic/schools`, `/academic/schools/[id]`,
`/academic/grades`, `/academic/grades/[id]`,
`/academic/courses`, `/academic/courses/[id]`

---

## 6. Descripción de dominios

### auth
- Usuarios, login, logout, refresh tokens
- Tablas: `users`, `refresh_tokens`
- JWT access token (30 min, httpOnly cookie)
- Refresh token (64 bytes random, SHA256 hash en DB, revocable)

### rbac
- Roles, permisos, asignación usuario-rol, asignación rol-permiso
- Permisos como strings: `{domain}.{resource}.{action}`
- Ejemplos: `commercial.sales_order.approve`, `production.batch.update_status`
- Tablas: `roles`, `permissions`, `role_permissions`, `user_roles`

### audit
- Registro de toda acción relevante: quién, qué, sobre qué recurso, cuándo
- Tabla: `audit_logs`
- Crítico desde el inicio — la plataforma mueve stock, dinero y producción

### catalog
- Fuente de verdad de productos
- Tipos: `KIT`, `COMPONENT`
- Un kit tiene BOM ligero (`kit_bom_items`)
- Chasis tratado como componente en BOM, pero con biblioteca de archivos de corte láser (por kit/grado/colegio)
- Tablas: `products`, `kit_bom_items`

### commercial
- Órdenes de venta como fuente comercial interna
- Orígenes: `WOO`, `POS`, `MANUAL`
- Mientras está pendiente, el origen externo puede modificarla
- Al aprobar: se congela snapshot, se dispara fulfillment + check de stock + producción si hace falta
- Tablas: `sales_orders`, `sales_order_items`

### inventory
- Inventario de kits terminados: agregado por producto + ubicación + estado
- Inventario de componentes: agregado por componente + ubicación + estado
- No hay serialización por unidad individual
- Reserva = movimiento de `FREE` → `RESERVED_WEB` o `RESERVED_FAIR`
- Tablas: `stock_locations`, `inventory_balances`, `inventory_movements`, `component_inventory_balances`, `component_inventory_movements`

### production
- Unidad central: `ProductionBatch`
- Tipos de batch: `SALES`, `STOCK`, `FAIR`, `MANUAL`
- Se produce solo lo faltante (no el total de la orden)
- Hora de corte diaria: el sistema agrupa órdenes y genera batch automáticamente
- El administrador puede intervenir manualmente (prioridad, inclusión/exclusión)
- Genera: hoja maestra del batch, tirillas de contenido optimizadas, tickets de envío
- Tablas: `production_batches`, `production_batch_sales_orders`, `production_batch_items`, `production_item_counters`, `production_blocks`

### fulfillment
- Packing flow por orden de venta
- QR de orden: abre contexto operativo de la orden
- QR de kit: confirma que el kit correcto entra en el packing
- Componentes sueltos: confirmación manual por cantidad
- Consolidación de envíos: misma dirección → un solo envío
- Tablas: `sales_order_pack_items`, `sales_order_pack_events`

### integrations
- Sync con WooCommerce (webhooks + cron fallback)
- Sync con Wompi (confirmación de pagos)
- Estado de última sincronización
- Tabla: `integration_sync_state`

### academic
- LMS para colegios aliados
- Jerarquía: Colegio → Grado (Director) → Curso (Teacher) → Estudiante
- Roles académicos: ADMIN, DIRECTOR, TEACHER, STUDENT
- Contenido: Unidades → Materiales (PDF, TEXT, VIDEO, LINK) + Tareas
- Entregas de estudiantes con calificación por docente
- Storage en MinIO para PDFs de materiales y archivos de entregas
- Tablas: `schools`, `lms_grades`, `lms_grade_directors`, `lms_courses`,
  `lms_course_students`, `lms_units`, `lms_materials`, `lms_assignments`,
  `lms_submissions`

---

## 7. Seguridad

- JWT access token en cookie `httpOnly` (no expuesto a JS)
- Refresh token: random 64 bytes, guardado como SHA256 hash en DB
- Refresh tokens son revocables y tienen expiración
- RBAC por strings de permiso, validados en backend
- Auditoría desde día uno
- `public_id` (UUID) expuesto en APIs, `id` interno nunca expuesto
- QR tokens son opacos — no contienen datos sensibles

---

## 8. Modelo de datos

El modelo completo está en `db.sql` (formato DBML) en la raíz del repo.

### Todas las tablas migradas

`users`, `refresh_tokens`, `roles`, `permissions`, `role_permissions`,
`user_roles`, `audit_logs`, `products`, `kit_bom_items`, `sales_orders`,
`sales_order_items`, `sales_order_pack_items`, `sales_order_pack_events`,
`production_batches`, `production_batch_sales_orders`, `production_batch_items`,
`production_item_counters`, `production_blocks`, `stock_locations`,
`inventory_balances`, `inventory_movements`, `component_inventory_balances`,
`component_inventory_movements`, `integration_sync_state`,
`schools`, `lms_grades`, `lms_grade_directors`, `lms_courses`,
`lms_course_students`, `lms_units`, `lms_materials`, `lms_assignments`,
`lms_submissions`

---

## 9. Reglas de arquitectura

1. **No inventar features** fuera del modelo acordado
2. **Respetar límites de dominio** — un dominio no accede a la capa interna de otro
3. **Rutas delgadas** — lógica de negocio en servicios, no en rutas
4. **Persistencia en repositorios** — los servicios no escriben SQL directo
5. **Migraciones siempre con Alembic** — nunca modificar el schema manualmente
6. **MySQL 8** — no SQLite como fallback real
7. **Todo corre en contenedores** — Docker para dev y prod
8. **No exponer PII en QR** — tokens opacos sin datos sensibles
9. **Código explícito** — evitar abstracciones excesivas
10. **Cada dominio completo** — modelos + schemas + repos + servicios + rutas + migración + tests mínimos

---

## 10. Docker Compose

### Servicios (dev)
| Servicio | Imagen | Puerto |
|---|---|---|
| mysql | mysql:8.0 | 3306 |
| minio | minio/minio:latest | 9000 (S3), 9001 (console) |
| backend | build ./backend | 8000 |
| frontend | build ./frontend | 3000 |
| nginx | nginx:1.27-alpine | 8080→80 |

### Notas importantes
- En dev, usar un `.env` real (copiado de `.env.example`), no el `.env.example` directamente
- `secret_key` debe generarse con `openssl rand -hex 32` antes de usar
- `database_url` apunta al nombre del servicio Docker (`mysql:3306`), correcto para la red interna