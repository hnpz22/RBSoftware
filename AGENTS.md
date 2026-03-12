# MIEL - Agent Rules (Current MVP+ Foundation)

## Fixed stack
- Backend: FastAPI (Python) + SQLModel + Alembic
- DB: MySQL 8
- Frontend: Next.js + React + TypeScript
- UI: Tailwind + shadcn/ui
- Forms: React Hook Form
- State: Context + Zustand
- Storage: MinIO (S3 compatible)
- Infra: Docker + Docker Compose, Nginx reverse proxy
- API: REST + OpenAPI

## Monorepo layout
- /backend
- /frontend
- /infra
- compose.dev.yml
- compose.prod.yml

## Backend architecture: modular monolith by domain
backend/app/
  core/
  domains/
    auth/
    rbac/
    audit/
    catalog/
    commercial/
    fulfillment/
    production/
    inventory/
    integrations/

Each domain owns:
- models
- schemas
- services
- repositories
- routes

## Current scope
The system supports:
1. normal sales flow: sale -> approval -> stock check -> production if needed -> fulfillment -> shipping
2. anticipatory production for fair/stock
3. aggregated finished-goods balances by product + location + status
4. aggregated component inventory by product + location + status

## Core business model

### Catalog
- Unified Product catalog with types:
  - KIT
  - COMPONENT
- KIT has BOM light via kit_bom_items

### Commercial
- SalesOrder is the commercial source of truth inside the platform after approval
- Woo/Wompi may update orders while pending/unpaid
- Once approved/paid:
  - freeze SalesOrder snapshot
  - create fulfillment planning records
  - perform stock check
  - reserve stock if available
  - create production requirements only for missing quantities

### Fulfillment
- Sales orders have fulfillment workflow and QR order token
- Packing flow uses:
  - sales_order_pack_items
  - sales_order_pack_events
- Order QR opens operational context
- KIT product QR confirms required kit quantities
- Components are confirmed manually by quantity
- Closing packing changes order fulfillment_status to EMPACADO

### Production
- Aggregate operational concept is ProductionBatch
- Batches may be:
  - SALES
  - STOCK
  - FAIR
  - MANUAL
- Production creates only missing quantities, not total ordered quantities
- Blocks may reference missing components

### Inventory
- Finished goods inventory:
  - inventory_balances
  - inventory_movements
- Component inventory:
  - component_inventory_balances
  - component_inventory_movements
- Stock is aggregated by:
  - product
  - location
  - status

### Security
- Auth from day 1: JWT access + refresh in httpOnly cookies
- Refresh tokens stored in DB (hashed, revocable, expirable)
- RBAC: roles -> permissions strings
- Audit from day 1

## Guardrails
- Do not invent features outside the agreed data model
- Prefer explicit service logic over excessive abstraction
- Add migrations and tests for critical business flows
- Respect domain boundaries
- Keep app-layer validations for type restrictions (KIT vs COMPONENT)