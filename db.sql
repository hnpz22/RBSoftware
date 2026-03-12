// MIEL - Final consolidated data model
// Conventions:
// - Internal PK: int autoincrement
// - External/public id: uuid when needed
// - QR token is opaque and only useful inside the platform
// - MySQL 8 target
// - Scope:
//   1) normal sales flow: sale -> approval -> stock check -> production if needed -> fulfillment -> shipping
//   2) anticipatory production for fair/stock
//   3) aggregated finished-goods balances by product + location + status
//   4) aggregated component inventory by product + location + status

Enum product_type {
  KIT
  COMPONENT
}

Enum sales_order_source {
  WOO
  MANUAL
  POS
}

Enum sales_order_status {
  PENDING
  APPROVED
  CANCELLED
}

Enum fulfillment_status {
  PENDIENTE
  EN_CURSO
  EMPACADO
  ENVIADO
  ENTREGADA
  EN_PAUSA
  CANCELADO
}

Enum production_status {
  PENDING
  IN_PROGRESS
  READY
  PAUSED
  CANCELLED
}

Enum production_batch_kind {
  SALES
  STOCK
  FAIR
  MANUAL
}

Enum batch_link_mode {
  AUTO
  MANUAL
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
  PRODUCTION_OUTPUT
  RESERVE
  RELEASE_RESERVATION
  PACK
  SHIP
  DELIVER
  TRANSFER_OUT
  TRANSFER_IN
  ADJUSTMENT_IN
  ADJUSTMENT_OUT
  MARK_TO_DISASSEMBLE
}

Enum pack_event_type {
  ORDER_SCANNED
  PICK_CONFIRMED
  PACK_CONFIRMED
  SHIP_CONFIRMED
  DELIVERY_CONFIRMED
  REOPENED
}

Enum component_stock_status {
  AVAILABLE
  BLOCKED
  DAMAGED
  RESERVED
}

Enum component_movement_type {
  PURCHASE_IN
  MANUAL_IN
  MANUAL_OUT
  TRANSFER_OUT
  TRANSFER_IN
  PRODUCTION_CONSUMPTION
  PRODUCTION_RETURN
  ADJUSTMENT_IN
  ADJUSTMENT_OUT
  MARK_BLOCKED
  MARK_DAMAGED
  UNBLOCK
}

// --------------------
// Auth + RBAC + Audit
// --------------------
Table users {
  id int [pk, increment]
  public_id uuid [unique, not null]
  email varchar(190) [not null, unique]
  password_hash varchar(255) [not null]
  is_active boolean [not null, default: true]
  created_at datetime [not null]
  updated_at datetime [not null]
}

Table refresh_tokens {
  id int [pk, increment]
  user_id int [not null, ref: > users.id]
  token_hash varchar(255) [not null]
  issued_at datetime [not null]
  expires_at datetime [not null]
  revoked_at datetime
  revoked_reason varchar(255)
  created_at datetime [not null]

  Indexes {
    (user_id)
    (expires_at)
  }
}

Table roles {
  id int [pk, increment]
  public_id uuid [unique, not null]
  name varchar(80) [not null, unique]
  description varchar(255)
  created_at datetime [not null]
  updated_at datetime [not null]
}

Table permissions {
  id int [pk, increment]
  public_id uuid [unique, not null]
  code varchar(160) [not null, unique] // e.g. production.batch.update_status
  description varchar(255)
  created_at datetime [not null]
}

Table role_permissions {
  id int [pk, increment]
  role_id int [not null, ref: > roles.id]
  permission_id int [not null, ref: > permissions.id]
  created_at datetime [not null]

  Indexes {
    (role_id, permission_id) [unique]
  }
}

Table user_roles {
  id int [pk, increment]
  user_id int [not null, ref: > users.id]
  role_id int [not null, ref: > roles.id]
  created_at datetime [not null]

  Indexes {
    (user_id, role_id) [unique]
  }
}

Table audit_logs {
  id int [pk, increment]
  actor_user_id int [ref: > users.id]
  action varchar(160) [not null]
  resource_type varchar(120) [not null]
  resource_id int
  metadata_json json
  created_at datetime [not null]

  Indexes {
    (actor_user_id, created_at)
    (resource_type, resource_id)
  }
}

// --------------------
// Catalog
// --------------------
Table products {
  id int [pk, increment]
  public_id uuid [unique, not null]
  type product_type [not null]
  sku varchar(80) [unique]
  name varchar(180) [not null]
  price decimal(12,2) [not null]
  active boolean [not null, default: true]

  // Generic QR for kits during picking/packing workflow
  qr_code varchar(120) [unique]

  created_at datetime [not null]
  updated_at datetime [not null]
  created_by int [ref: > users.id]
  updated_by int [ref: > users.id]

  Indexes {
    (type)
  }
}

Table kit_bom_items {
  id int [pk, increment]
  kit_id int [not null, ref: > products.id]        // must be KIT at app layer
  component_id int [not null, ref: > products.id]  // must be COMPONENT at app layer
  required_qty decimal(12,3) [not null]
  created_at datetime [not null]

  Indexes {
    (kit_id, component_id) [unique]
  }
}

// --------------------
// Commercial
// --------------------
Table sales_orders {
  id int [pk, increment]
  public_id uuid [unique, not null]
  source sales_order_source [not null]
  external_id varchar(120)
  status sales_order_status [not null]
  fulfillment_status fulfillment_status [not null, default: 'PENDIENTE']

  // QR token to open order context in platform
  qr_token varchar(160) [not null, unique]

  approved_at datetime
  approved_by int [ref: > users.id]
  date_modified_external datetime

  frozen_snapshot_json json
  customer_snapshot_json json

  packed_at datetime
  packed_by int [ref: > users.id]
  shipped_at datetime
  shipped_by int [ref: > users.id]
  delivered_at datetime
  delivered_by int [ref: > users.id]

  created_at datetime [not null]
  updated_at datetime [not null]
  created_by int [ref: > users.id]
  updated_by int [ref: > users.id]

  Indexes {
    (status, created_at)
    (fulfillment_status, created_at)
    (external_id)
  }
}

Table sales_order_items {
  id int [pk, increment]
  sales_order_id int [not null, ref: > sales_orders.id]
  product_id int [not null, ref: > products.id] // KIT or COMPONENT
  qty int [not null]
  price_snapshot decimal(12,2) [not null]
  meta_json json
  created_at datetime [not null]

  Indexes {
    (sales_order_id)
    (product_id)
  }
}

// --------------------
// Fulfillment planning per sales order
// Created when sales order becomes APPROVED
// --------------------
Table sales_order_pack_items {
  id int [pk, increment]
  sales_order_item_id int [not null, ref: > sales_order_items.id]
  product_id int [not null, ref: > products.id] // denormalized for fast ops
  required_qty_snapshot int [not null]
  verified_qty int [not null, default: 0]
  requires_scan boolean [not null, default: false] // true for KIT, false for manual component confirmation
  last_verified_at datetime
  last_verified_by int [ref: > users.id]
  created_at datetime [not null]
  updated_at datetime [not null]

  Indexes {
    (sales_order_item_id) [unique]
    (product_id)
  }
}

Table sales_order_pack_events {
  id int [pk, increment]
  sales_order_id int [not null, ref: > sales_orders.id]
  sales_order_pack_item_id int [ref: > sales_order_pack_items.id]
  actor_user_id int [ref: > users.id]
  event_type pack_event_type [not null]
  product_id int [ref: > products.id]
  qty_delta int
  metadata_json json
  created_at datetime [not null]

  Indexes {
    (sales_order_id, created_at)
    (sales_order_pack_item_id, created_at)
    (actor_user_id, created_at)
    (event_type, created_at)
  }
}

// --------------------
// Production
// Daily batches generate only missing quantities
// A batch may be linked to sales orders or be anticipatory stock production
// --------------------
Table production_batches {
  id int [pk, increment]
  public_id uuid [unique, not null]
  batch_code varchar(80) [unique, not null]
  batch_date date [not null]
  batch_kind production_batch_kind [not null]
  status production_status [not null]
  rules_json json
  notes text
  created_at datetime [not null]
  updated_at datetime [not null]
  created_by int [ref: > users.id]
  updated_by int [ref: > users.id]

  Indexes {
    (batch_date)
    (status, batch_date)
    (batch_kind, batch_date)
  }
}

Table production_batch_sales_orders {
  id int [pk, increment]
  production_batch_id int [not null, ref: > production_batches.id]
  sales_order_id int [not null, ref: > sales_orders.id]
  mode batch_link_mode [not null] // AUTO or MANUAL
  added_by int [ref: > users.id]
  added_at datetime [not null]

  Indexes {
    (sales_order_id)
    (production_batch_id, sales_order_id) [unique]
  }
}

Table production_batch_items {
  id int [pk, increment]
  production_batch_id int [not null, ref: > production_batches.id]
  product_id int [not null, ref: > products.id] // should be KIT at app layer
  required_qty_total int [not null]             // requested by linked orders or production plan
  available_stock_qty int [not null, default: 0]
  to_produce_qty int [not null]                 // actual missing qty to produce
  notes text
  created_at datetime [not null]

  Indexes {
    (production_batch_id, product_id) [unique]
  }
}

Table production_item_counters {
  id int [pk, increment]
  production_batch_item_id int [not null, ref: > production_batch_items.id]
  status production_status [not null]
  qty int [not null]
  updated_at datetime [not null]
  updated_by int [ref: > users.id]

  Indexes {
    (production_batch_item_id, status) [unique]
  }
}

Table production_blocks {
  id int [pk, increment]
  production_batch_id int [not null, ref: > production_batches.id]
  component_product_id int [ref: > products.id] // should be COMPONENT at app layer
  reason varchar(255) [not null]
  created_at datetime [not null]
  created_by int [ref: > users.id]
  resolved_at datetime
  resolved_by int [ref: > users.id]

  Indexes {
    (production_batch_id, resolved_at)
    (component_product_id)
  }
}

// --------------------
// Shared locations
// --------------------
Table stock_locations {
  id int [pk, increment]
  public_id uuid [unique, not null]
  code varchar(80) [not null, unique]   // e.g. BODEGA_PRINCIPAL, FERIA_USME, COLEGIO_X
  name varchar(150) [not null]
  description varchar(255)
  active boolean [not null, default: true]
  created_at datetime [not null]
  updated_at datetime [not null]
}

// --------------------
// Finished goods / sellable inventory balances
// Can hold KIT and optionally COMPONENT if sold as standalone finished goods
// Only FREE is available for fresh allocations
// --------------------
Table inventory_balances {
  id int [pk, increment]
  product_id int [not null, ref: > products.id]
  stock_location_id int [not null, ref: > stock_locations.id]
  stock_status stock_status [not null]
  qty int [not null, default: 0]
  updated_at datetime [not null]

  Indexes {
    (product_id, stock_location_id, stock_status) [unique]
    (stock_location_id, stock_status)
  }
}

Table inventory_movements {
  id int [pk, increment]
  product_id int [not null, ref: > products.id]
  movement_type stock_movement_type [not null]

  from_stock_location_id int [ref: > stock_locations.id]
  to_stock_location_id int [ref: > stock_locations.id]

  from_status stock_status
  to_status stock_status

  qty int [not null]
  sales_order_id int [ref: > sales_orders.id]
  production_batch_id int [ref: > production_batches.id]

  reason varchar(255)
  metadata_json json

  created_at datetime [not null]
  created_by int [ref: > users.id]

  Indexes {
    (product_id, created_at)
    (sales_order_id, created_at)
    (production_batch_id, created_at)
    (movement_type, created_at)
  }
}

// --------------------
// Component inventory
// Uses products(type = COMPONENT) + stock_locations
// --------------------
Table component_inventory_balances {
  id int [pk, increment]
  product_id int [not null, ref: > products.id] // should be COMPONENT at app layer
  stock_location_id int [not null, ref: > stock_locations.id]
  stock_status component_stock_status [not null, default: 'AVAILABLE']
  qty decimal(12,3) [not null, default: 0]
  updated_at datetime [not null]

  Indexes {
    (product_id, stock_location_id, stock_status) [unique]
    (stock_location_id, stock_status)
  }
}

Table component_inventory_movements {
  id int [pk, increment]
  product_id int [not null, ref: > products.id] // should be COMPONENT at app layer
  movement_type component_movement_type [not null]

  from_stock_location_id int [ref: > stock_locations.id]
  to_stock_location_id int [ref: > stock_locations.id]

  from_status component_stock_status
  to_status component_stock_status

  qty decimal(12,3) [not null]
  production_batch_id int [ref: > production_batches.id]
  production_batch_item_id int [ref: > production_batch_items.id]

  reason varchar(255)
  metadata_json json

  created_at datetime [not null]
  created_by int [ref: > users.id]

  Indexes {
    (product_id, created_at)
    (production_batch_id, created_at)
    (production_batch_item_id, created_at)
    (movement_type, created_at)
  }
}

// --------------------
// Integrations
// --------------------
Table integration_sync_state {
  id int [pk, increment]
  provider varchar(50) [not null, unique] // e.g. woo, wompi
  last_sync datetime [not null]
  updated_at datetime [not null]
}