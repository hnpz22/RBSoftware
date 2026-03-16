'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, CheckCircle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import type { SalesOrder, StockLocation } from '@/lib/types'

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    PENDING: 'warning', UNPAID: 'info', APPROVED: 'success',
    CANCELLED: 'destructive', REFUNDED: 'muted',
  }
  return <Badge variant={(map[status] ?? 'outline') as any}>{status}</Badge>
}

export default function OrderDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()

  const [order, setOrder] = useState<SalesOrder | null>(null)
  const [locations, setLocations] = useState<StockLocation[]>([])
  const [selectedLocation, setSelectedLocation] = useState('')
  const [approving, setApproving] = useState(false)
  const [showApproveForm, setShowApproveForm] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function loadOrder() {
    try {
      const data = await api.get<SalesOrder>(`/commercial/orders/${id}`)
      setOrder(data)
    } catch {
      setError('Orden no encontrada')
    }
  }

  useEffect(() => {
    loadOrder()
    api.get<StockLocation[]>('/inventory/locations').then(setLocations).catch(() => {})
  }, [id])

  async function handleApprove() {
    if (!selectedLocation) return
    setApproving(true)
    setError(null)
    try {
      await api.post(`/commercial/orders/${id}/approve`, { location_id: selectedLocation })
      await loadOrder()
      setShowApproveForm(false)
    } catch (err: any) {
      setError(err.detail ?? 'Error al aprobar')
    } finally {
      setApproving(false)
    }
  }

  if (error && !order) {
    return (
      <div className="space-y-4">
        <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft size={14} /> Volver
        </button>
        <p className="text-destructive">{error}</p>
      </div>
    )
  }

  if (!order) {
    return <div className="text-sm text-muted-foreground">Cargando…</div>
  }

  const canApprove = order.status === 'PENDING' || order.status === 'UNPAID'

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft size={14} /> Volver
        </button>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">{order.customer_name}</h1>
          <p className="text-sm text-muted-foreground">{order.customer_email}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={order.status} />
          {canApprove && !showApproveForm && (
            <Button size="sm" onClick={() => setShowApproveForm(true)}>
              <CheckCircle size={14} className="mr-1" />
              Aprobar
            </Button>
          )}
        </div>
      </div>

      {/* Approve form */}
      {showApproveForm && canApprove && (
        <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
          <p className="text-sm font-medium">Seleccionar ubicación de stock</p>
          <select
            className="w-full rounded-md border bg-background px-3 py-2 text-sm"
            value={selectedLocation}
            onChange={(e) => setSelectedLocation(e.target.value)}
          >
            <option value="">— Seleccionar ubicación —</option>
            {locations.map((loc) => (
              <option key={loc.public_id} value={loc.public_id}>
                {loc.name} ({loc.type})
              </option>
            ))}
          </select>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <div className="flex gap-2">
            <Button size="sm" onClick={handleApprove} disabled={!selectedLocation || approving}>
              {approving ? 'Aprobando…' : 'Confirmar aprobación'}
            </Button>
            <Button size="sm" variant="outline" onClick={() => { setShowApproveForm(false); setError(null) }}>
              Cancelar
            </Button>
          </div>
        </div>
      )}

      {/* Info grid */}
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div className="space-y-1">
          <p className="text-muted-foreground">Teléfono</p>
          <p>{order.customer_phone ?? '—'}</p>
        </div>
        <div className="space-y-1">
          <p className="text-muted-foreground">Fuente</p>
          <p>{order.source}</p>
        </div>
        <div className="space-y-1">
          <p className="text-muted-foreground">Fulfillment</p>
          <p>{order.fulfillment_status}</p>
        </div>
        <div className="space-y-1">
          <p className="text-muted-foreground">ID externo</p>
          <p>{order.external_id ?? '—'}</p>
        </div>
        {order.qr_token && (
          <div className="col-span-2 space-y-1">
            <p className="text-muted-foreground">QR token</p>
            <p className="font-mono text-xs break-all">{order.qr_token}</p>
          </div>
        )}
        {order.shipping_address && (
          <div className="col-span-2 space-y-1">
            <p className="text-muted-foreground">Dirección de envío</p>
            <p>{order.shipping_address}</p>
          </div>
        )}
        {order.notes && (
          <div className="col-span-2 space-y-1">
            <p className="text-muted-foreground">Notas</p>
            <p>{order.notes}</p>
          </div>
        )}
      </div>

      {/* Items */}
      <div>
        <h2 className="mb-3 text-base font-medium">Productos</h2>
        <div className="rounded-lg border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-2 text-left font-medium">SKU / Nombre</th>
                <th className="px-4 py-2 text-right font-medium">Cantidad</th>
                <th className="px-4 py-2 text-right font-medium">Precio unit.</th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item) => (
                <tr key={item.id} className="border-b last:border-0">
                  <td className="px-4 py-2">
                    {item.snapshot_sku ? (
                      <>
                        <span className="font-mono text-xs">{item.snapshot_sku}</span>
                        <span className="ml-2 text-muted-foreground">{item.snapshot_name}</span>
                      </>
                    ) : (
                      <span className="text-muted-foreground">Producto #{item.product_id}</span>
                    )}
                  </td>
                  <td className="px-4 py-2 text-right">{item.quantity}</td>
                  <td className="px-4 py-2 text-right">{item.unit_price}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
