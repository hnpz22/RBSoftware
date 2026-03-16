'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { ChevronRight, Plus, RefreshCw, Search, Trash2, X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { Product, SalesOrder } from '@/lib/types'

// ── Status helpers ─────────────────────────────────────────────────────────────

function orderStatusVariant(status: string) {
  switch (status) {
    case 'PENDING': return 'warning'
    case 'UNPAID': return 'info'
    case 'APPROVED': return 'success'
    case 'CANCELLED': return 'destructive'
    case 'REFUNDED': return 'muted'
    default: return 'outline'
  }
}

function fulfillmentVariant(status: string) {
  switch (status) {
    case 'PENDING': return 'muted'
    case 'IN_PROGRESS': return 'info'
    case 'PACKED': return 'purple'
    case 'SHIPPED': return 'success'
    case 'DELIVERED': return 'success'
    default: return 'outline'
  }
}

// ── Types ─────────────────────────────────────────────────────────────────────

interface OrderItemDraft {
  product: Product
  quantity: number
  unit_price: string
}

const EMPTY_FORM = {
  customer_name: '',
  customer_email: '',
  customer_phone: '',
  shipping_address: '',
  notes: '',
  source: 'MANUAL' as 'MANUAL' | 'POS',
}

// ── New Order Modal ────────────────────────────────────────────────────────────

function NewOrderModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState(EMPTY_FORM)
  const [items, setItems] = useState<OrderItemDraft[]>([])
  const [search, setSearch] = useState('')
  const [searchResults, setSearchResults] = useState<Product[]>([])
  const [searching, setSearching] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const searchRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  function setField(key: keyof typeof EMPTY_FORM, value: string) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  // Debounced product search
  useEffect(() => {
    if (search.trim().length < 2) {
      setSearchResults([])
      return
    }
    if (searchRef.current) clearTimeout(searchRef.current)
    searchRef.current = setTimeout(async () => {
      setSearching(true)
      try {
        const results = await api.get<Product[]>(`/catalog/products?search=${encodeURIComponent(search.trim())}`)
        setSearchResults(results)
      } catch {
        setSearchResults([])
      } finally {
        setSearching(false)
      }
    }, 300)
  }, [search])

  function addItem(product: Product) {
    if (items.some((i) => i.product.public_id === product.public_id)) return
    setItems((prev) => [...prev, { product, quantity: 1, unit_price: '0' }])
    setSearch('')
    setSearchResults([])
  }

  function removeItem(publicId: string) {
    setItems((prev) => prev.filter((i) => i.product.public_id !== publicId))
  }

  function updateItem(publicId: string, field: 'quantity' | 'unit_price', value: string) {
    setItems((prev) =>
      prev.map((i) =>
        i.product.public_id === publicId ? { ...i, [field]: value } : i,
      ),
    )
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (items.length === 0) {
      setError('Agrega al menos un producto.')
      return
    }
    setSaving(true)
    try {
      await api.post('/commercial/orders', {
        source: form.source,
        customer_name: form.customer_name,
        customer_email: form.customer_email,
        customer_phone: form.customer_phone || null,
        shipping_address: form.shipping_address || null,
        notes: form.notes || null,
        items: items.map((i) => ({
          product_public_id: i.product.public_id,
          quantity: Number(i.quantity),
          unit_price: i.unit_price,
        })),
      })
      onCreated()
    } catch (err: any) {
      setError(err?.detail ?? 'Error al crear la orden')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="relative max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg border bg-card shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">Nueva orden</h2>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6 px-6 py-5">
          {/* Source */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Fuente
            </label>
            <div className="flex gap-2">
              {(['MANUAL', 'POS'] as const).map((src) => (
                <button
                  key={src}
                  type="button"
                  onClick={() => setField('source', src)}
                  className={`rounded-md border px-4 py-1.5 text-sm font-medium transition-colors ${
                    form.source === src
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-input hover:bg-muted'
                  }`}
                >
                  {src}
                </button>
              ))}
            </div>
          </div>

          {/* Customer */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Cliente
            </label>
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <Input
                  required
                  placeholder="Nombre completo"
                  value={form.customer_name}
                  onChange={(e) => setField('customer_name', e.target.value)}
                />
              </div>
              <Input
                required
                type="email"
                placeholder="Email"
                value={form.customer_email}
                onChange={(e) => setField('customer_email', e.target.value)}
              />
              <Input
                placeholder="Teléfono"
                value={form.customer_phone}
                onChange={(e) => setField('customer_phone', e.target.value)}
              />
            </div>
          </div>

          {/* Shipping address */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Dirección de envío
            </label>
            <textarea
              rows={2}
              placeholder="Dirección completa..."
              value={form.shipping_address}
              onChange={(e) => setField('shipping_address', e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Notes */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Notas
            </label>
            <textarea
              rows={2}
              placeholder="Observaciones internas..."
              value={form.notes}
              onChange={(e) => setField('notes', e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Items */}
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              Productos
            </label>

            {/* Product search */}
            <div className="relative">
              <div className="relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Buscar por nombre o SKU..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-8"
                />
              </div>
              {(searchResults.length > 0 || searching) && (
                <div className="absolute z-10 mt-1 w-full rounded-md border bg-card shadow-lg">
                  {searching && (
                    <div className="px-3 py-2 text-sm text-muted-foreground">Buscando…</div>
                  )}
                  {searchResults.map((p) => (
                    <button
                      key={p.public_id}
                      type="button"
                      onClick={() => addItem(p)}
                      className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-muted"
                    >
                      <span className="font-mono text-xs text-muted-foreground">{p.sku}</span>
                      <span>{p.name}</span>
                      <span className="ml-auto text-xs text-muted-foreground">{p.type}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Items table */}
            {items.length > 0 && (
              <div className="rounded-md border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="px-3 py-2 text-left font-medium">Producto</th>
                      <th className="px-3 py-2 text-left font-medium w-20">Cant.</th>
                      <th className="px-3 py-2 text-left font-medium w-28">Precio unit.</th>
                      <th className="px-3 py-2 w-8" />
                    </tr>
                  </thead>
                  <tbody>
                    {items.map((item) => (
                      <tr key={item.product.public_id} className="border-b last:border-0">
                        <td className="px-3 py-2">
                          <p className="font-medium">{item.product.name}</p>
                          <p className="text-xs text-muted-foreground">{item.product.sku}</p>
                        </td>
                        <td className="px-3 py-2">
                          <Input
                            type="number"
                            min={1}
                            value={item.quantity}
                            onChange={(e) => updateItem(item.product.public_id, 'quantity', e.target.value)}
                            className="h-8 w-16 text-sm"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <Input
                            type="number"
                            min={0}
                            step="0.01"
                            placeholder="0.00"
                            value={item.unit_price}
                            onChange={(e) => updateItem(item.product.public_id, 'unit_price', e.target.value)}
                            className="h-8 w-24 text-sm"
                          />
                        </td>
                        <td className="px-3 py-2">
                          <button
                            type="button"
                            onClick={() => removeItem(item.product.public_id)}
                            className="text-muted-foreground hover:text-destructive"
                          >
                            <Trash2 size={14} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}

          {/* Actions */}
          <div className="flex justify-end gap-2 border-t pt-4">
            <Button type="button" variant="outline" onClick={onClose} disabled={saving}>
              Cancelar
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? 'Guardando…' : 'Crear orden'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function OrdersPage() {
  const [orders, setOrders] = useState<SalesOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const data = await api.get<SalesOrder[]>('/commercial/orders')
      setOrders(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  function handleCreated() {
    setShowModal(false)
    load()
  }

  return (
    <>
      {showModal && (
        <NewOrderModal onClose={() => setShowModal(false)} onCreated={handleCreated} />
      )}

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Órdenes</h1>
            <p className="text-sm text-muted-foreground">{orders.length} registros</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={load} disabled={loading}>
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              <span className="ml-2">Actualizar</span>
            </Button>
            <Button size="sm" onClick={() => setShowModal(true)}>
              <Plus size={14} />
              <span className="ml-2">Nueva orden</span>
            </Button>
          </div>
        </div>

        <div className="rounded-lg border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Cliente</th>
                <th className="px-4 py-3 text-left font-medium">Estado</th>
                <th className="px-4 py-3 text-left font-medium">Fulfillment</th>
                <th className="px-4 py-3 text-left font-medium">Fuente</th>
                <th className="px-4 py-3 text-left font-medium">Creado por</th>
                <th className="px-4 py-3 text-left font-medium">Fecha</th>
                <th className="px-4 py-3 text-left font-medium" />
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                    Cargando…
                  </td>
                </tr>
              )}
              {!loading && orders.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-4 py-8 text-center text-muted-foreground">
                    No hay órdenes
                  </td>
                </tr>
              )}
              {orders.map((order) => (
                <tr key={order.public_id} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="px-4 py-3">
                    <p className="font-medium">{order.customer_name}</p>
                    <p className="text-xs text-muted-foreground">{order.customer_email}</p>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={orderStatusVariant(order.status) as any}>
                      {order.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={fulfillmentVariant(order.fulfillment_status) as any}>
                      {order.fulfillment_status}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">{order.source}</td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {(order.source === 'MANUAL' || order.source === 'POS')
                      ? (order.created_by_name ?? '—')
                      : '—'}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {new Date(order.created_at).toLocaleDateString('es-ES')}
                  </td>
                  <td className="px-4 py-3">
                    <Link href={`/orders/${order.public_id}`}>
                      <ChevronRight size={16} className="text-muted-foreground hover:text-foreground" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
