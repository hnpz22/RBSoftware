'use client'

import { useEffect, useState } from 'react'
import { RefreshCw, Plus, X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ErrorBanner } from '@/components/error-banner'
import { Pagination } from '@/components/pagination'
import { useToast } from '@/components/ui/use-toast'
import { api } from '@/lib/api'
import type { LocationRead, Product, StockAlert } from '@/lib/types'

const ITEMS_PER_PAGE = 20

// ── Semaphore dot ─────────────────────────────────────────────────────────────

const DOT_CLASS: Record<string, string> = {
  RED:    'bg-red-500',
  YELLOW: 'bg-yellow-400',
  GREEN:  'bg-green-500',
}

function Dot({ color }: { color: string }) {
  return (
    <span
      className={`inline-block h-2.5 w-2.5 rounded-full ${DOT_CLASS[color] ?? 'bg-muted'}`}
    />
  )
}

// ── Color filter config ───────────────────────────────────────────────────────

type ColorFilter = 'ALL' | 'RED' | 'YELLOW' | 'GREEN'

const COLOR_BUTTONS: { value: ColorFilter; label: string }[] = [
  { value: 'ALL',    label: 'Todos' },
  { value: 'RED',    label: '🔴 Sin stock' },
  { value: 'YELLOW', label: '🟡 Stock bajo' },
  { value: 'GREEN',  label: '🟢 OK' },
]

// ── Section tabs ──────────────────────────────────────────────────────────────

type Section = 'balances' | 'locations'

// ── Main ──────────────────────────────────────────────────────────────────────

export default function InventoryPage() {
  const [section, setSection] = useState<Section>('balances')
  const { toast } = useToast()

  // Alerts state
  const [alerts, setAlerts] = useState<StockAlert[]>([])
  const [colorFilter, setColorFilter] = useState<ColorFilter>('ALL')
  const [loadingAlerts, setLoadingAlerts] = useState(true)
  const [alertsError, setAlertsError] = useState<string | null>(null)
  const [alertsPage, setAlertsPage] = useState(1)

  // Locations state
  const [locations, setLocations] = useState<LocationRead[]>([])
  const [loadingLocations, setLoadingLocations] = useState(false)
  const [locationsError, setLocationsError] = useState<string | null>(null)

  // New location form
  const [showLocationForm, setShowLocationForm] = useState(false)
  const [locForm, setLocForm] = useState({ name: '', type: 'WAREHOUSE', address: '' })
  const [locSaving, setLocSaving] = useState(false)

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

  // Read ?color= param on mount to pre-filter (e.g. from dashboard link)
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const color = params.get('color')?.toUpperCase()
    if (color === 'RED' || color === 'YELLOW' || color === 'GREEN') {
      setColorFilter(color)
    }
  }, [])

  async function loadAlerts() {
    setLoadingAlerts(true)
    setAlertsError(null)
    try {
      const data = await api.get<StockAlert[]>('/inventory/alerts')
      setAlerts(data)
      setAlertsPage(1)
    } catch (err: any) {
      setAlertsError(err?.detail ?? 'Error al cargar el inventario. Verifica tu conexión.')
    } finally {
      setLoadingAlerts(false)
    }
  }

  async function loadLocations() {
    setLoadingLocations(true)
    setLocationsError(null)
    try {
      const data = await api.get<LocationRead[]>('/inventory/locations')
      setLocations(data)
    } catch (err: any) {
      setLocationsError(err?.detail ?? 'Error al cargar ubicaciones.')
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
    loadAlerts()
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
    setLocSaving(true)
    try {
      await api.post('/inventory/locations', {
        name: locForm.name.trim(),
        type: locForm.type,
        address: locForm.address.trim() || null,
      })
      setLocForm({ name: '', type: 'WAREHOUSE', address: '' })
      setShowLocationForm(false)
      toast({ title: 'Ubicación creada', variant: 'success' })
      await loadLocations()
    } catch (err: any) {
      toast({
        title: 'Error al crear la ubicación',
        description: err?.detail ?? 'Intenta de nuevo',
        variant: 'destructive',
      })
    } finally {
      setLocSaving(false)
    }
  }

  // ── Stock adjustment ─────────────────────────────────────────────────────────

  async function handleAdjust(e: React.FormEvent) {
    e.preventDefault()
    setAdjSaving(true)
    try {
      await api.post('/inventory/movements', {
        product_public_id: adjForm.product_public_id,
        location_public_id: adjForm.location_public_id,
        status: 'FREE',
        delta: parseInt(adjForm.delta, 10),
        notes: adjForm.notes.trim() || null,
      })
      toast({
        title: 'Stock ajustado',
        description: `+${adjForm.delta} unidades FREE registradas`,
        variant: 'success',
      })
      setAdjForm({ product_public_id: '', location_public_id: '', delta: '1', notes: '' })
      await loadAlerts()
    } catch (err: any) {
      toast({
        title: 'Error al ajustar stock',
        description: err?.detail ?? 'Intenta de nuevo',
        variant: 'destructive',
      })
    } finally {
      setAdjSaving(false)
    }
  }

  // ── Filtered alerts ───────────────────────────────────────────────────────────

  const filtered = colorFilter === 'ALL'
    ? alerts
    : alerts.filter((a) => a.status_color === colorFilter)

  const redCount    = alerts.filter((a) => a.status_color === 'RED').length
  const yellowCount = alerts.filter((a) => a.status_color === 'YELLOW').length
  const greenCount  = alerts.filter((a) => a.status_color === 'GREEN').length

  const alertsTotalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE)
  const paginatedAlerts = filtered.slice(
    (alertsPage - 1) * ITEMS_PER_PAGE,
    alertsPage * ITEMS_PER_PAGE,
  )

  // Reset page when filter changes
  useEffect(() => {
    setAlertsPage(1)
  }, [colorFilter])

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Inventario</h1>
        <Button
          variant="outline"
          size="sm"
          onClick={section === 'balances' ? loadAlerts : loadLocations}
          disabled={loadingAlerts || loadingLocations}
        >
          <RefreshCw size={14} className={(loadingAlerts || loadingLocations) ? 'animate-spin' : ''} />
          <span className="ml-2 hidden sm:inline">Actualizar</span>
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
          {alertsError && <ErrorBanner message={alertsError} onRetry={loadAlerts} />}

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-muted-foreground">
              {alerts.length} productos ·{' '}
              <span className="text-red-500 font-medium">{redCount} sin stock</span>
              {' · '}
              <span className="text-yellow-500 font-medium">{yellowCount} bajo</span>
              {' · '}
              <span className="text-green-600 font-medium">{greenCount} OK</span>
            </p>
            <Button
              size="sm"
              onClick={() => {
                setShowAdjustForm(true)
                loadLocations()
                loadProducts()
              }}
            >
              <Plus size={14} className="mr-1" />
              <span className="hidden sm:inline">Ajuste de inventario</span>
              <span className="sm:hidden">Ajustar</span>
            </Button>
          </div>

          {/* Stock adjust form */}
          {showAdjustForm && (
            <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">Registrar stock inicial / ajuste</p>
                <button onClick={() => setShowAdjustForm(false)}>
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
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
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
                    onClick={() => setShowAdjustForm(false)}
                  >
                    Cancelar
                  </Button>
                </div>
              </form>
            </div>
          )}

          {/* Color filter pills */}
          <div className="flex flex-wrap gap-2">
            {COLOR_BUTTONS.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => setColorFilter(value)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                  colorFilter === value
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:bg-muted/80'
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Alerts table */}
          <div className="overflow-x-auto -mx-4 sm:mx-0 rounded-lg border">
            <div className="inline-block min-w-full align-middle px-4 sm:px-0">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-3 text-left font-medium w-8">Estado</th>
                    <th className="px-4 py-3 text-left font-medium">Producto</th>
                    <th className="px-4 py-3 text-right font-medium w-28">Unidades FREE</th>
                  </tr>
                </thead>
                <tbody>
                  {loadingAlerts && (
                    <tr>
                      <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground">
                        Cargando…
                      </td>
                    </tr>
                  )}
                  {!loadingAlerts && !alertsError && filtered.length === 0 && (
                    <tr>
                      <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground">
                        {alerts.length === 0
                          ? 'Sin productos activos en catálogo.'
                          : 'No hay productos con ese estado.'}
                      </td>
                    </tr>
                  )}
                  {paginatedAlerts.map((alert) => (
                    <tr key={alert.product_id} className="border-b last:border-0">
                      <td className="px-4 py-3">
                        <Dot color={alert.status_color} />
                      </td>
                      <td className="px-4 py-3">
                        <p className="font-medium leading-tight">{alert.product_name}</p>
                        <p className="font-mono text-xs text-muted-foreground">{alert.sku}</p>
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums font-medium">
                        {alert.total_free}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <Pagination
            currentPage={alertsPage}
            totalPages={alertsTotalPages}
            onPageChange={setAlertsPage}
            totalItems={filtered.length}
            itemsPerPage={ITEMS_PER_PAGE}
          />
        </div>
      )}

      {/* ── LOCATIONS ── */}
      {section === 'locations' && (
        <div className="space-y-4">
          {locationsError && <ErrorBanner message={locationsError} onRetry={loadLocations} />}

          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">{locations.length} ubicaciones</p>
            <Button size="sm" onClick={() => setShowLocationForm(true)}>
              <Plus size={14} className="mr-1" />
              <span className="hidden sm:inline">Nueva ubicación</span>
              <span className="sm:hidden">Nueva</span>
            </Button>
          </div>

          {/* New location form */}
          {showLocationForm && (
            <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium">Nueva ubicación</p>
                <button onClick={() => setShowLocationForm(false)}>
                  <X size={16} className="text-muted-foreground hover:text-foreground" />
                </button>
              </div>
              <form onSubmit={handleCreateLocation} className="space-y-3">
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
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
                <div className="flex gap-2">
                  <Button type="submit" size="sm" disabled={locSaving}>
                    {locSaving ? 'Guardando…' : 'Crear ubicación'}
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => setShowLocationForm(false)}
                  >
                    Cancelar
                  </Button>
                </div>
              </form>
            </div>
          )}

          {/* Locations table */}
          <div className="overflow-x-auto -mx-4 sm:mx-0 rounded-lg border">
            <div className="inline-block min-w-full align-middle px-4 sm:px-0">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-3 text-left font-medium">Nombre</th>
                    <th className="px-4 py-3 text-left font-medium">Tipo</th>
                    <th className="hidden px-4 py-3 text-left font-medium sm:table-cell">Dirección</th>
                    <th className="hidden px-4 py-3 text-left font-medium sm:table-cell">Activa</th>
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
                  {!loadingLocations && !locationsError && locations.length === 0 && (
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
                      <td className="hidden px-4 py-3 text-muted-foreground text-xs sm:table-cell">
                        {loc.address ?? '—'}
                      </td>
                      <td className="hidden px-4 py-3 sm:table-cell">
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
        </div>
      )}
    </div>
  )
}
