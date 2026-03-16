'use client'

import { useEffect, useState } from 'react'
import { RefreshCw, Plus, X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { InventorySummaryItem, LocationRead, Product } from '@/lib/types'

// ── Helpers ───────────────────────────────────────────────────────────────────

const STATUS_VARIANT: Record<string, string> = {
  FREE: 'success',
  RESERVED_WEB: 'info',
  RESERVED_FAIR: 'info',
  PACKED: 'purple',
  SHIPPED: 'success',
  DELIVERED: 'success',
  BLOCKED: 'destructive',
  DAMAGED: 'destructive',
  LOST: 'muted',
}

function groupByProduct(rows: InventorySummaryItem[]) {
  const map = new Map<number, InventorySummaryItem[]>()
  for (const row of rows) {
    if (!map.has(row.product_id)) map.set(row.product_id, [])
    map.get(row.product_id)!.push(row)
  }
  return map
}

// ── Section tabs ──────────────────────────────────────────────────────────────

type Section = 'balances' | 'locations'

// ── Main ──────────────────────────────────────────────────────────────────────

export default function InventoryPage() {
  const [section, setSection] = useState<Section>('balances')

  // Balances state
  const [summary, setSummary] = useState<InventorySummaryItem[]>([])
  const [filterStatus, setFilterStatus] = useState<string>('ALL')
  const [loadingBalances, setLoadingBalances] = useState(true)

  // Locations state
  const [locations, setLocations] = useState<LocationRead[]>([])
  const [loadingLocations, setLoadingLocations] = useState(false)

  // New location form
  const [showLocationForm, setShowLocationForm] = useState(false)
  const [locForm, setLocForm] = useState({ name: '', type: 'WAREHOUSE', address: '' })
  const [locSaving, setLocSaving] = useState(false)
  const [locError, setLocError] = useState<string | null>(null)

  // Stock adjustment form
  const [showAdjustForm, setShowAdjustForm] = useState(false)
  const [products, setProducts] = useState<Product[]>([])
  const [adjForm, setAdjForm] = useState({
    product_public_id: '',
    location_public_id: '',
    delta: '1',
    notes: '',
  })
  const [adjSaving, setAdjSaving] = useState(false)
  const [adjError, setAdjError] = useState<string | null>(null)
  const [adjSuccess, setAdjSuccess] = useState<string | null>(null)

  async function loadBalances() {
    setLoadingBalances(true)
    try {
      const data = await api.get<InventorySummaryItem[]>('/inventory/balances/summary')
      setSummary(data)
    } finally {
      setLoadingBalances(false)
    }
  }

  async function loadLocations() {
    setLoadingLocations(true)
    try {
      const data = await api.get<LocationRead[]>('/inventory/locations')
      setLocations(data)
    } finally {
      setLoadingLocations(false)
    }
  }

  async function loadProducts() {
    try {
      const data = await api.get<Product[]>('/catalog/products?is_active=true')
      setProducts(data.filter((p) => p.type === 'KIT'))
    } catch {
      setProducts([])
    }
  }

  useEffect(() => {
    loadBalances()
  }, [])

  useEffect(() => {
    if (section === 'locations') {
      loadLocations()
      loadProducts()
    }
  }, [section])

  // ── Location create ──────────────────────────────────────────────────────────

  async function handleCreateLocation(e: React.FormEvent) {
    e.preventDefault()
    setLocError(null)
    setLocSaving(true)
    try {
      await api.post('/inventory/locations', {
        name: locForm.name.trim(),
        type: locForm.type,
        address: locForm.address.trim() || null,
      })
      setLocForm({ name: '', type: 'WAREHOUSE', address: '' })
      setShowLocationForm(false)
      await loadLocations()
    } catch (err: any) {
      setLocError(err.detail ?? 'Error al crear la ubicación')
    } finally {
      setLocSaving(false)
    }
  }

  // ── Stock adjustment ─────────────────────────────────────────────────────────

  async function handleAdjust(e: React.FormEvent) {
    e.preventDefault()
    setAdjError(null)
    setAdjSuccess(null)
    setAdjSaving(true)
    try {
      await api.post('/inventory/movements', {
        product_public_id: adjForm.product_public_id,
        location_public_id: adjForm.location_public_id,
        status: 'FREE',
        delta: parseInt(adjForm.delta, 10),
        notes: adjForm.notes.trim() || null,
      })
      setAdjSuccess(`Stock ajustado: +${adjForm.delta} unidades FREE`)
      setAdjForm({ product_public_id: '', location_public_id: '', delta: '1', notes: '' })
      await loadBalances()
    } catch (err: any) {
      setAdjError(err.detail ?? 'Error al ajustar stock')
    } finally {
      setAdjSaving(false)
    }
  }

  // ── Balances section ─────────────────────────────────────────────────────────

  const statuses = ['ALL', ...Array.from(new Set(summary.map((s) => s.status))).sort()]
  const filtered = filterStatus === 'ALL' ? summary : summary.filter((s) => s.status === filterStatus)
  const grouped = groupByProduct(filtered)

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Inventario</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={section === 'balances' ? loadBalances : loadLocations}
          disabled={loadingBalances || loadingLocations}
        >
          <RefreshCw size={14} className={(loadingBalances || loadingLocations) ? 'animate-spin' : ''} />
          <span className="ml-2">Actualizar</span>
        </Button>
      </div>

      {/* Section tabs */}
      <div className="flex gap-2 border-b pb-0">
        {(['balances', 'locations'] as Section[]).map((s) => (
          <button
            key={s}
            onClick={() => setSection(s)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              section === s
                ? 'border-primary text-foreground'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {s === 'balances' ? 'Balances de stock' : 'Ubicaciones'}
          </button>
        ))}
      </div>

      {/* ── BALANCES ── */}
      {section === 'balances' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {grouped.size} productos · {filtered.length} líneas
            </p>
            <Button
              size="sm"
              onClick={() => { setShowAdjustForm(true); setAdjError(null); setAdjSuccess(null) }}
            >
              <Plus size={14} className="mr-1" />
              Ajuste de inventario
            </Button>
          </div>

          {/* Stock adjust form */}
          {showAdjustForm && (
            <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">Registrar stock inicial / ajuste</p>
                <button onClick={() => { setShowAdjustForm(false); setAdjError(null); setAdjSuccess(null) }}>
                  <X size={16} className="text-muted-foreground hover:text-foreground" />
                </button>
              </div>
              <form onSubmit={handleAdjust} className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-medium">Producto (KIT)</label>
                  <select
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                    value={adjForm.product_public_id}
                    onChange={(e) => setAdjForm({ ...adjForm, product_public_id: e.target.value })}
                    required
                  >
                    <option value="">— Seleccionar producto —</option>
                    {products.map((p) => (
                      <option key={p.public_id} value={p.public_id}>
                        {p.sku} — {p.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-medium">Ubicación</label>
                    <select
                      className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                      value={adjForm.location_public_id}
                      onChange={(e) => setAdjForm({ ...adjForm, location_public_id: e.target.value })}
                      required
                    >
                      <option value="">— Seleccionar ubicación —</option>
                      {locations.map((loc) => (
                        <option key={loc.public_id} value={loc.public_id}>
                          {loc.name} ({loc.type})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium">Cantidad</label>
                    <Input
                      type="number"
                      min="1"
                      value={adjForm.delta}
                      onChange={(e) => setAdjForm({ ...adjForm, delta: e.target.value })}
                      required
                    />
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium">Nota (opcional)</label>
                  <Input
                    placeholder="ej. Stock inicial bodega"
                    value={adjForm.notes}
                    onChange={(e) => setAdjForm({ ...adjForm, notes: e.target.value })}
                  />
                </div>
                {adjError && <p className="text-sm text-destructive">{adjError}</p>}
                {adjSuccess && <p className="text-sm text-green-600">{adjSuccess}</p>}
                <div className="flex gap-2">
                  <Button
                    type="submit"
                    size="sm"
                    disabled={adjSaving || !adjForm.product_public_id || !adjForm.location_public_id}
                  >
                    {adjSaving ? 'Guardando…' : 'Registrar stock'}
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => { setShowAdjustForm(false); setAdjError(null); setAdjSuccess(null) }}
                  >
                    Cancelar
                  </Button>
                </div>
              </form>
            </div>
          )}

          {/* Status filter pills */}
          <div className="flex flex-wrap gap-2">
            {statuses.map((s) => (
              <button
                key={s}
                onClick={() => setFilterStatus(s)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  filterStatus === s
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                {s}
              </button>
            ))}
          </div>

          {/* Balances table */}
          <div className="rounded-lg border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium">Producto ID</th>
                  <th className="px-4 py-3 text-left font-medium">Estado</th>
                  <th className="px-4 py-3 text-right font-medium">Cantidad</th>
                </tr>
              </thead>
              <tbody>
                {loadingBalances && (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground">
                      Cargando…
                    </td>
                  </tr>
                )}
                {!loadingBalances && grouped.size === 0 && (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground">
                      Sin datos. Usa "Ajuste de inventario" para registrar stock.
                    </td>
                  </tr>
                )}
                {Array.from(grouped.entries()).map(([productId, rows]) =>
                  rows.map((row, i) => (
                    <tr key={`${productId}-${row.status}`} className="border-b last:border-0">
                      {i === 0 && (
                        <td
                          className="px-4 py-2 font-mono text-xs text-muted-foreground align-top"
                          rowSpan={rows.length}
                        >
                          #{productId}
                        </td>
                      )}
                      <td className="px-4 py-2">
                        <Badge variant={(STATUS_VARIANT[row.status] ?? 'outline') as any}>
                          {row.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-2 text-right font-medium">{row.total_quantity}</td>
                    </tr>
                  )),
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── LOCATIONS ── */}
      {section === 'locations' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">{locations.length} ubicaciones</p>
            <Button size="sm" onClick={() => { setShowLocationForm(true); setLocError(null) }}>
              <Plus size={14} className="mr-1" />
              Nueva ubicación
            </Button>
          </div>

          {/* New location form */}
          {showLocationForm && (
            <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">Nueva ubicación</p>
                <button onClick={() => { setShowLocationForm(false); setLocError(null) }}>
                  <X size={16} className="text-muted-foreground hover:text-foreground" />
                </button>
              </div>
              <form onSubmit={handleCreateLocation} className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-medium">Nombre</label>
                    <Input
                      placeholder="ej. Bodega Norte"
                      value={locForm.name}
                      onChange={(e) => setLocForm({ ...locForm, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium">Tipo</label>
                    <select
                      className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                      value={locForm.type}
                      onChange={(e) => setLocForm({ ...locForm, type: e.target.value })}
                    >
                      <option value="WAREHOUSE">WAREHOUSE</option>
                      <option value="SEDE">SEDE</option>
                      <option value="FAIR">FAIR</option>
                      <option value="SCHOOL">SCHOOL</option>
                    </select>
                  </div>
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium">Dirección (opcional)</label>
                  <Input
                    placeholder="ej. Calle 100 #15-30, Bogotá"
                    value={locForm.address}
                    onChange={(e) => setLocForm({ ...locForm, address: e.target.value })}
                  />
                </div>
                {locError && <p className="text-sm text-destructive">{locError}</p>}
                <div className="flex gap-2">
                  <Button type="submit" size="sm" disabled={locSaving}>
                    {locSaving ? 'Guardando…' : 'Crear ubicación'}
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => { setShowLocationForm(false); setLocError(null) }}
                  >
                    Cancelar
                  </Button>
                </div>
              </form>
            </div>
          )}

          {/* Locations table */}
          <div className="rounded-lg border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium">Nombre</th>
                  <th className="px-4 py-3 text-left font-medium">Tipo</th>
                  <th className="px-4 py-3 text-left font-medium">Dirección</th>
                  <th className="px-4 py-3 text-left font-medium">Activa</th>
                </tr>
              </thead>
              <tbody>
                {loadingLocations && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                      Cargando…
                    </td>
                  </tr>
                )}
                {!loadingLocations && locations.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                      Sin ubicaciones. Ejecuta el seed o crea una manualmente.
                    </td>
                  </tr>
                )}
                {locations.map((loc) => (
                  <tr key={loc.public_id} className="border-b last:border-0">
                    <td className="px-4 py-3 font-medium">{loc.name}</td>
                    <td className="px-4 py-3">
                      <Badge variant="outline">{loc.type}</Badge>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground text-xs">
                      {loc.address ?? '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={loc.is_active ? 'text-green-600' : 'text-muted-foreground'}>
                        {loc.is_active ? 'Sí' : 'No'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
