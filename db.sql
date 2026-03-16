// RBSoftware — Modelo de datos completo
// Formato: DBML (dbdiagram.io)
// Última actualización: 2026-03-15
// Fuente de verdad del schema. Toda migración debe partir de aquí.

// ─────────────────────────────────────────────
// ENUMS
// ─────────────────────────────────────────────

Enum product_type {
  KIT
  COMPONENT
}

Enum sales_order_source {
  WOO
  POS
  MANUAL
}

Enum sales_order_status {
  PENDING
  UNPAID
  APPROVED
  CANCELLED
  REFUNDED
}

Enum fulfillment_status {
  PENDING
  IN_PROGRESS
  PACKED
  SHIPPED
  DELIVERED
  CANCELLED
}

Enum production_status {
  PENDING
  IN_PROGRESS
  DONE
  CANCELLED
}

Enum production_batch_kind {
  SALES
  STOCK
  FAIR
  MANUAL
}

Enum batch_link_mode {
  FULL
  PARTIAL
}

Enum stock_status {
  FREE
  RESERVED_WEB
  RESERVED_FAIR
  PACKED
  SHIPPED
  DELIVERED
  TO_DISASSEMBLE
  LOST
  DAMAGED
  BLOCKED
}

Enum stock_movement_type {
  IN
  OUT
  TRANSFER
  RESERVE
  RELEASE
  ADJUST
}

Enum pack_event_type {
  KIT_SCANNED
  COMPONENT_CONFIRMED
  PACK_CLOSED
  PACK_REOPENED
}

Enum component_stock_status {
  AVAILABLE
  BLOCKED
  DAMAGED
  RESERVED
}

Enum component_movement_type {
  IN
  OUT
  RESERVE
  RELEASE
  CONSUME
  ADJUST
}

// ─────────────────────────────────────────────
// AUTH
// ─────────────────────────────────────────────

Table users {
  id            int           [pk, increment]
  public_id     varchar(36)   [unique, not null]  // UUID expuesto en API
  email         varchar(255)  [unique, not null]
  password_hash varchar(255)  [not null]
  first_name    varchar(100)  [not null]
  last_name     varchar(100)  [not null]
  phone         varchar(30)   [null]
  position      varchar(100)  [null]              // cargo / puesto
  is_active     boolean       [not null, default: true]
  created_at    datetime      [not null]
  updated_at    datetime      [not null]

  // Nota: actores externos (clientes, colegios, padres) también usarán
  // esta tabla en fases futuras. Las tablas de perfil extendido
  // (ej. student_profiles, school_contacts) se asociarán por user_id.
}

Table refresh_tokens {
  id            int           [pk, increment]
  public_id     varchar(36)   [unique, not null]
  user_id       int           [not null, ref: > users.id]
  token_hash    varchar(255)  [unique, not null]  // SHA256 del token real
  expires_at    datetime      [not null]
  revoked_at    datetime      [null]
  created_at    datetime      [not null]
  updated_at    datetime      [not null]
}

// ─────────────────────────────────────────────
// RBAC
// ─────────────────────────────────────────────

Table roles {
  id            int           [pk, increment]
  public_id     varchar(36)   [unique, not null]
  name          varchar(100)  [unique, not null]
  description   varchar(255)  [null]
  created_at    datetime      [not null]
  updated_at    datetime      [not null]
}

Table permissions {
  id            int           [pk, increment]
  public_id     varchar(36)   [unique, not null]
  code          varchar(150)  [unique, not null]  // ej: commercial.sales_order.approve
  description   varchar(255)  [null]
  created_at    datetime      [not null]
  updated_at    datetime      [not null]
}

Table role_permissions {
  id              int     [pk, increment]
  role_id         int     [not null, ref: > roles.id]
  permission_id   int     [not null, ref: > permissions.id]
  created_at      datetime [not null]
  updated_at      datetime [not null]

  indexes {
    (role_id, permission_id) [unique]
  }
}

Table user_roles {
  id          int     [pk, increment]
  user_id     int     [not null, ref: > users.id]
  role_id     int     [not null, ref: > roles.id]
  created_at  datetime [not null]
  updated_at  datetime [not null]

  indexes {
    (user_id, role_id) [unique]
  }
}

// ─────────────────────────────────────────────
// AUDIT
// ─────────────────────────────────────────────

Table audit_logs {
  id            int           [pk, increment]
  user_id       int           [null, ref: > users.id]  // null si fue sistema
  action        varchar(100)  [not null]   // ej: sales_order.approve
  resource_type varchar(100)  [not null]   // ej: sales_order
  resource_id   varchar(36)   [not null]   // public_id del recurso
  payload       json          [null]       // datos relevantes del cambio
  ip_address    varchar(50)   [null]
  created_at    datetime      [not null]
}

// ─────────────────────────────────────────────
// CATALOG
// ─────────────────────────────────────────────

Table products {
  id              int           [pk, increment]
  public_id       varchar(36)   [unique, not null]
  sku             varchar(100)  [unique, not null]
  name            varchar(255)  [not null]
  type            product_type  [not null]         // KIT o COMPONENT
  description     text          [null]
  qr_code         varchar(255)  [null]             // QR genérico del producto
  is_active       boolean       [not null, default: true]
  // Para chasis: referencia a archivo de corte láser almacenado en MinIO
  cut_file_key    varchar(500)  [null]             // key en MinIO (solo COMPONENT tipo chasis)
  cut_file_notes  text          [null]             // notas sobre el archivo de corte
  created_at      datetime      [not null]
  updated_at      datetime      [not null]
}

Table kit_bom_items {
  id              int     [pk, increment]
  kit_id          int     [not null, ref: > products.id]       // debe ser KIT
  component_id    int     [not null, ref: > products.id]       // debe ser COMPONENT
  quantity        int     [not null]
  notes           text    [null]
  created_at      datetime [not null]
  updated_at      datetime [not null]

  indexes {
    (kit_id, component_id) [unique]
  }
}

// ─────────────────────────────────────────────
// COMMERCIAL
// ─────────────────────────────────────────────

Table sales_orders {
  id                  int               [pk, increment]
  public_id           varchar(36)       [unique, not null]
  external_id         varchar(100)      [null]         // ID en WooCommerce u origen externo
  source              sales_order_source [not null]
  status              sales_order_status [not null, default: 'PENDING']
  fulfillment_status  fulfillment_status [not null, default: 'PENDING']
  customer_name       varchar(255)      [null]
  customer_email      varchar(255)      [null]
  customer_phone      varchar(30)       [null]
  shipping_address    text              [null]
  billing_address     text              [null]
  notes               text              [null]
  qr_token            varchar(100)      [unique, null]  // token opaco para QR de orden
  approved_at         datetime          [null]
  snapshot_frozen_at  datetime          [null]          // cuándo se congeló el snapshot
  created_at          datetime          [not null]
  updated_at          datetime          [not null]
}

Table sales_order_items {
  id              int     [pk, increment]
  sales_order_id  int     [not null, ref: > sales_orders.id]
  product_id      int     [not null, ref: > products.id]
  quantity        int     [not null]
  unit_price      decimal(12,2) [not null]  // precio al momento de la orden
  snapshot_name   varchar(255) [not null]   // nombre del producto al momento de congelar
  snapshot_sku    varchar(100) [not null]   // SKU al momento de congelar
  created_at      datetime [not null]
  updated_at      datetime [not null]
}

// ─────────────────────────────────────────────
// FULFILLMENT
// ─────────────────────────────────────────────

Table sales_order_pack_items {
  id              int     [pk, increment]
  sales_order_id  int     [not null, ref: > sales_orders.id]
  product_id      int     [not null, ref: > products.id]
  required_qty    int     [not null]
  confirmed_qty   int     [not null, default: 0]
  created_at      datetime [not null]
  updated_at      datetime [not null]
}

Table sales_order_pack_events {
  id              int             [pk, increment]
  sales_order_id  int             [not null, ref: > sales_orders.id]
  product_id      int             [null, ref: > products.id]
  event_type      pack_event_type [not null]
  quantity        int             [null]
  scanned_qr      varchar(255)    [null]
  performed_by    int             [null, ref: > users.id]
  notes           text            [null]
  created_at      datetime        [not null]
}

// ─────────────────────────────────────────────
// PRODUCTION
// ─────────────────────────────────────────────

Table production_batches {
  id              int                   [pk, increment]
  public_id       varchar(36)           [unique, not null]
  kind            production_batch_kind [not null]
  status          production_status     [not null, default: 'PENDING']
  name            varchar(255)          [null]
  notes           text                  [null]
  cutoff_at       datetime              [null]  // hora de corte que originó el batch
  started_at      datetime              [null]
  completed_at    datetime              [null]
  created_by      int                   [null, ref: > users.id]
  created_at      datetime              [not null]
  updated_at      datetime              [not null]
}

Table production_batch_sales_orders {
  id              int             [pk, increment]
  batch_id        int             [not null, ref: > production_batches.id]
  sales_order_id  int             [not null, ref: > sales_orders.id]
  link_mode       batch_link_mode [not null]
  created_at      datetime        [not null]
  updated_at      datetime        [not null]

  indexes {
    (batch_id, sales_order_id) [unique]
  }
}

Table production_batch_items {
  id                  int     [pk, increment]
  batch_id            int     [not null, ref: > production_batches.id]
  product_id          int     [not null, ref: > products.id]
  required_qty_total  int     [not null]
  available_stock_qty int     [not null, default: 0]
  to_produce_qty      int     [not null]  // = required_qty_total - available_stock_qty
  produced_qty        int     [not null, default: 0]
  created_at          datetime [not null]
  updated_at          datetime [not null]
}

Table production_item_counters {
  id              int     [pk, increment]
  batch_item_id   int     [not null, ref: > production_batch_items.id]
  counted_by      int     [null, ref: > users.id]
  count           int     [not null]
  notes           text    [null]
  created_at      datetime [not null]
}

Table production_blocks {
  id              int     [pk, increment]
  batch_item_id   int     [not null, ref: > production_batch_items.id]
  component_id    int     [not null, ref: > products.id]
  missing_qty     int     [not null]
  resolved_at     datetime [null]
  notes           text    [null]
  created_at      datetime [not null]
  updated_at      datetime [not null]
}

// ─────────────────────────────────────────────
// INVENTORY
// ─────────────────────────────────────────────

Table stock_locations {
  id          int           [pk, increment]
  public_id   varchar(36)   [unique, not null]
  name        varchar(100)  [not null]
  type        varchar(50)   [not null]   // WAREHOUSE, SEDE, FAIR, SCHOOL
  address     text          [null]
  is_active   boolean       [not null, default: true]
  created_at  datetime      [not null]
  updated_at  datetime      [not null]
}

Table inventory_balances {
  id              int           [pk, increment]
  product_id      int           [not null, ref: > products.id]
  location_id     int           [not null, ref: > stock_locations.id]
  status          stock_status  [not null]
  quantity        int           [not null, default: 0]
  updated_at      datetime      [not null]

  indexes {
    (product_id, location_id, status) [unique]
  }
}

Table inventory_movements {
  id              int                 [pk, increment]
  product_id      int                 [not null, ref: > products.id]
  location_id     int                 [not null, ref: > stock_locations.id]
  movement_type   stock_movement_type [not null]
  quantity        int                 [not null]
  from_status     stock_status        [null]
  to_status       stock_status        [null]
  sales_order_id  int                 [null, ref: > sales_orders.id]
  batch_id        int                 [null, ref: > production_batches.id]
  performed_by    int                 [null, ref: > users.id]
  notes           text                [null]
  created_at      datetime            [not null]
}

Table component_inventory_balances {
  id              int                   [pk, increment]
  component_id    int                   [not null, ref: > products.id]
  location_id     int                   [not null, ref: > stock_locations.id]
  status          component_stock_status [not null]
  quantity        int                   [not null, default: 0]
  updated_at      datetime              [not null]

  indexes {
    (component_id, location_id, status) [unique]
  }
}

Table component_inventory_movements {
  id              int                     [pk, increment]
  component_id    int                     [not null, ref: > products.id]
  location_id     int                     [not null, ref: > stock_locations.id]
  movement_type   component_movement_type [not null]
  quantity        int                     [not null]
  from_status     component_stock_status  [null]
  to_status       component_stock_status  [null]
  batch_id        int                     [null, ref: > production_batches.id]
  performed_by    int                     [null, ref: > users.id]
  notes           text                    [null]
  created_at      datetime                [not null]
}

// ─────────────────────────────────────────────
// INTEGRATIONS
// ─────────────────────────────────────────────

Table integration_sync_state {
  id                int           [pk, increment]
  integration_name  varchar(100)  [unique, not null]  // ej: woocommerce, wompi
  last_synced_at    datetime      [null]
  last_cursor       varchar(255)  [null]   // cursor o ID del último objeto sincronizado
  status            varchar(50)   [null]   // OK, ERROR, SYNCING
  error_message     text          [null]
  created_at        datetime      [not null]
  updated_at        datetime      [not null]
}

// ─────────────────────────────────────────────
// DOMINIOS FUTUROS (Fase 2 y Fase 3)
// No implementar hasta completar MVP
// ─────────────────────────────────────────────

// FASE 2: suppliers, supplier_products, purchase_orders,
//         schools (colegios como entidad), school_contracts,
//         school_delivery_groups

// FASE 3 — Escuela interna:
//         courses, course_enrollments, class_sessions,
//         attendance_records, student_profiles

// FASE 3 — LMS para colegios:
//         lms_courses, lms_assignments, lms_submissions,
//         lms_materials, teacher_profiles