'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { ArrowLeft, Search, Trash2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { Product, SalesOrder } from '@/lib/types'

// ── Types ─────────────────────────────────────────────────────────────────────

interface ItemDraft {
  product: Product
  quantity: number
  unit_price: string
}

// ── Product search ─────────────────────────────────────────────────────────────

function ProductSearch({ onSelect }: { onSelect: (p: Product) => void }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Product[]>([])
  const [searching, setSearching] = useState(false)
  const [open, setOpen] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const wrapperRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([])
      setOpen(false)
      return
    }
    if (timerRef.current) clearTimeout(timerRef.current)
    timerRef.current = setTimeout(async () => {
      setSearching(true)
      try {
        const data = await api.get<Product[]>(
          `/catalog/products?search=${encodeURIComponent(query.trim())}`,
        )
        setResults(data)
        setOpen(true)
      } catch {
        setResults([])
      } finally {
        setSearching(false)
      }
    }, 300)
  }, [query])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  function handleSelect(p: Product) {
    onSelect(p)
    setQuery('')
    setResults([])
    setOpen(false)
  }

  return (
    <div ref={wrapperRef} className="relative">
      <div className="relative">
        <Search
          size={14}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
        />
        <Input
          placeholder="Buscar producto por nombre o SKU…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setOpen(true)}
          className="pl-8"
        />
      </div>

      {open && (
        <div className="absolute z-20 mt-1 w-full overflow-hidden rounded-md border bg-card shadow-lg">
          {searching && (
            <div className="px-3 py-2.5 text-sm text-muted-foreground">Buscando…</div>
          )}
          {!searching && results.length === 0 && (
            <div className="px-3 py-2.5 text-sm text-muted-foreground">Sin resultados</div>
          )}
          {results.map((p) => (
            <button
              key={p.public_id}
              type="button"
              onMouseDown={() => handleSelect(p)}
              className="flex w-full items-center gap-3 px-3 py-2.5 text-sm hover:bg-muted"
            >
              <span className="w-24 shrink-0 truncate font-mono text-xs text-muted-foreground">
                {p.sku}
              </span>
              <span className="flex-1 truncate text-left">{p.name}</span>
              <span className="shrink-0 rounded-sm bg-muted px-1.5 py-0.5 text-[10px] font-medium">
                {p.type}
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

const SOURCES = ['MANUAL', 'POS'] as const
type Source = (typeof SOURCES)[number]

export default function NewOrderPage() {
  const router = useRouter()

  // Form state
  const [source, setSource] = useState<Source>('MANUAL')
  const [customerName, setCustomerName] = useState('')
  const [customerEmail, setCustomerEmail] = useState('')
  const [customerPhone, setCustomerPhone] = useState('')
  const [shippingAddress, setShippingAddress] = useState('')
  const [notes, setNotes] = useState('')
  const [items, setItems] = useState<ItemDraft[]>([])

  // Submit state
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // ── Items helpers ────────────────────────────────────────────────────────────

  function addItem(product: Product) {
    if (items.some((i) => i.product.public_id === product.public_id)) return
    setItems((prev) => [...prev, { product, quantity: 1, unit_price: '' }])
  }

  function removeItem(publicId: string) {
    setItems((prev) => prev.filter((i) => i.product.public_id !== publicId))
  }

  function updateItem(publicId: string, field: 'quantity' | 'unit_price', value: string) {
    setItems((prev) =>
      prev.map((i) => (i.product.public_id === publicId ? { ...i, [field]: value } : i)),
    )
  }

  // ── Total ────────────────────────────────────────────────────────────────────

  const total = items.reduce((sum, i) => {
    const qty = Math.max(0, Number(i.quantity) || 0)
    const price = Math.max(0, parseFloat(i.unit_price) || 0)
    return sum + qty * price
  }, 0)

  // ── Submit ───────────────────────────────────────────────────────────────────

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)

    if (items.length === 0) {
      setError('Agrega al menos un producto a la orden.')
      return
    }

    const invalidPrice = items.find((i) => i.unit_price.trim() === '' || parseFloat(i.unit_price) < 0)
    if (invalidPrice) {
      setError(`Ingresa un precio válido para "${invalidPrice.product.name}".`)
      return
    }

    setSaving(true)
    try {
      const order = await api.post<SalesOrder>('/commercial/orders', {
        source,
        customer_name: customerName.trim(),
        customer_email: customerEmail.trim(),
        customer_phone: customerPhone.trim() || null,
        shipping_address: shippingAddress.trim() || null,
        notes: notes.trim() || null,
        items: items.map((i) => ({
          product_public_id: i.product.public_id,
          quantity: Math.max(1, Number(i.quantity)),
          unit_price: i.unit_price,
        })),
      })
      router.push(`/orders/${order.public_id}`)
    } catch (err: any) {
      setError(err?.detail ?? 'Error al crear la orden. Verifica los datos e intenta de nuevo.')
      setSaving(false)
    }
  }

  // ── Render ───────────────────────────────────────────────────────────────────

  return (
    <form onSubmit={handleSubmit} className="mx-auto max-w-3xl space-y-6">
      {/* Breadcrumb + actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Link href="/orders" className="flex items-center gap-1 hover:text-foreground">
            <ArrowLeft size={14} />
            Órdenes
          </Link>
          <span>/</span>
          <span className="text-foreground">Nueva orden</span>
        </div>
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => router.push('/orders')}
            disabled={saving}
          >
            Cancelar
          </Button>
          <Button type="submit" size="sm" disabled={saving}>
            {saving ? 'Creando…' : 'Crear orden'}
          </Button>
        </div>
      </div>

      <h1 className="text-2xl font-semibold">Nueva orden</h1>

      {/* ── Fuente ── */}
      <section className="rounded-lg border bg-card p-5 space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Fuente
        </h2>
        <div className="flex gap-2">
          {SOURCES.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => setSource(s)}
              className={`rounded-md border px-5 py-2 text-sm font-medium transition-colors ${
                source === s
                  ? 'border-primary bg-primary text-primary-foreground'
                  : 'border-input hover:bg-muted'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </section>

      {/* ── Cliente ── */}
      <section className="rounded-lg border bg-card p-5 space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Cliente
        </h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="sm:col-span-2 space-y-1.5">
            <label className="text-xs font-medium">
              Nombre completo <span className="text-destructive">*</span>
            </label>
            <Input
              required
              placeholder="Ej. María García"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium">
              Email <span className="text-destructive">*</span>
            </label>
            <Input
              required
              type="email"
              placeholder="cliente@email.com"
              value={customerEmail}
              onChange={(e) => setCustomerEmail(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium">
              Teléfono <span className="text-muted-foreground">(opcional)</span>
            </label>
            <Input
              placeholder="+57 300 000 0000"
              value={customerPhone}
              onChange={(e) => setCustomerPhone(e.target.value)}
            />
          </div>
          <div className="sm:col-span-2 space-y-1.5">
            <label className="text-xs font-medium">
              Dirección de envío <span className="text-muted-foreground">(opcional)</span>
            </label>
            <textarea
              rows={2}
              placeholder="Calle 123 # 45-67, Bogotá…"
              value={shippingAddress}
              onChange={(e) => setShippingAddress(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <div className="sm:col-span-2 space-y-1.5">
            <label className="text-xs font-medium">
              Notas internas <span className="text-muted-foreground">(opcional)</span>
            </label>
            <textarea
              rows={2}
              placeholder="Observaciones para el equipo…"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
        </div>
      </section>

      {/* ── Productos ── */}
      <section className="rounded-lg border bg-card p-5 space-y-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
          Productos
        </h2>

        <ProductSearch onSelect={addItem} />

        {items.length === 0 ? (
          <p className="rounded-md border border-dashed py-8 text-center text-sm text-muted-foreground">
            Busca y selecciona productos para agregarlos a la orden
          </p>
        ) : (
          <div className="overflow-hidden rounded-md border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-2.5 text-left font-medium">Producto</th>
                  <th className="px-4 py-2.5 text-left font-medium w-24">Cantidad</th>
                  <th className="px-4 py-2.5 text-left font-medium w-32">Precio unit.</th>
                  <th className="px-4 py-2.5 text-right font-medium w-28">Subtotal</th>
                  <th className="px-4 py-2.5 w-8" />
                </tr>
              </thead>
              <tbody>
                {items.map((item) => {
                  const qty = Math.max(0, Number(item.quantity) || 0)
                  const price = Math.max(0, parseFloat(item.unit_price) || 0)
                  const subtotal = qty * price
                  return (
                    <tr key={item.product.public_id} className="border-b last:border-0">
                      <td className="px-4 py-3">
                        <p className="font-medium leading-tight">{item.product.name}</p>
                        <p className="font-mono text-xs text-muted-foreground">{item.product.sku}</p>
                      </td>
                      <td className="px-4 py-3">
                        <Input
                          type="number"
                          min={1}
                          value={item.quantity}
                          onChange={(e) =>
                            updateItem(item.product.public_id, 'quantity', e.target.value)
                          }
                          className="h-8 w-20 text-sm"
                        />
                      </td>
                      <td className="px-4 py-3">
                        <Input
                          type="number"
                          min={0}
                          step="0.01"
                          placeholder="0.00"
                          value={item.unit_price}
                          onChange={(e) =>
                            updateItem(item.product.public_id, 'unit_price', e.target.value)
                          }
                          className="h-8 w-28 text-sm"
                        />
                      </td>
                      <td className="px-4 py-3 text-right tabular-nums text-muted-foreground">
                        {subtotal.toLocaleString('es-CO', {
                          minimumFractionDigits: 0,
                          maximumFractionDigits: 2,
                        })}
                      </td>
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          onClick={() => removeItem(item.product.public_id)}
                          className="text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
              <tfoot>
                <tr className="border-t bg-muted/30">
                  <td
                    colSpan={3}
                    className="px-4 py-2.5 text-right text-sm font-medium"
                  >
                    Total
                  </td>
                  <td className="px-4 py-2.5 text-right text-sm font-semibold tabular-nums">
                    {total.toLocaleString('es-CO', {
                      minimumFractionDigits: 0,
                      maximumFractionDigits: 2,
                    })}
                  </td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </section>

      {/* Error */}
      {error && (
        <p className="rounded-md bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </p>
      )}

      {/* Bottom actions */}
      <div className="flex justify-end gap-2 pb-6">
        <Button
          type="button"
          variant="outline"
          onClick={() => router.push('/orders')}
          disabled={saving}
        >
          Cancelar
        </Button>
        <Button type="submit" disabled={saving}>
          {saving ? 'Creando…' : 'Crear orden'}
        </Button>
      </div>
    </form>
  )
}
