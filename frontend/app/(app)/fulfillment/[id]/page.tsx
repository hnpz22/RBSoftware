'use client'

import { useCallback, useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, CheckCircle2, Package, Send, Scan } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { PackStatusResponse, PackItem, SalesOrder } from '@/lib/types'

const FULFILLMENT_VARIANT: Record<string, string> = {
  PENDING: 'muted', IN_PROGRESS: 'info', PACKED: 'purple', SHIPPED: 'success',
}

function ItemRow({ item }: { item: PackItem }) {
  const complete = item.confirmed_qty >= item.required_qty
  const pct = Math.min(100, Math.round((item.confirmed_qty / item.required_qty) * 100))
  return (
    <div className={`rounded-lg border p-3 ${complete ? 'border-green-200 bg-green-50' : ''}`}>
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">Producto #{item.product_id}</span>
        <span className={`font-medium ${complete ? 'text-green-700' : 'text-amber-600'}`}>
          {item.confirmed_qty} / {item.required_qty}
        </span>
      </div>
      <div className="mt-2 h-1.5 rounded-full bg-muted">
        <div
          className={`h-full rounded-full transition-all ${complete ? 'bg-green-500' : 'bg-amber-400'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

export default function PackingPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()

  const [order, setOrder] = useState<SalesOrder | null>(null)
  const [pack, setPack] = useState<PackStatusResponse | null>(null)
  const [kitQr, setKitQr] = useState('')
  const [scanning, setScanning] = useState(false)
  const [scanMsg, setScanMsg] = useState<{ text: string; ok: boolean } | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const loadPack = useCallback(async () => {
    try {
      const data = await api.get<PackStatusResponse>(`/fulfillment/orders/${id}/pack-status`)
      setPack(data)
    } catch {
      // 404 — no pack items yet, that's OK
    }
  }, [id])

  useEffect(() => {
    api.get<SalesOrder>(`/commercial/orders/${id}`).then(setOrder).catch(() => {})
    loadPack()
  }, [id, loadPack])

  async function initPacking() {
    if (!order?.qr_token) return
    setActionLoading(true)
    try {
      const data = await api.post<PackStatusResponse>('/fulfillment/scan/order', {
        qr_token: order.qr_token,
      })
      setPack(data)
    } catch (err: any) {
      setActionError(err.detail ?? 'Error al inicializar')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleScanKit(e: React.FormEvent) {
    e.preventDefault()
    if (!kitQr.trim()) return
    setScanMsg(null)
    setScanning(true)
    try {
      await api.post(`/fulfillment/scan/kit`, {
        order_public_id: id,
        product_qr: kitQr.trim(),
      })
      setKitQr('')
      setScanMsg({ text: 'Item confirmado ✓', ok: true })
      await loadPack()
    } catch (err: any) {
      setScanMsg({ text: err.detail ?? 'QR no reconocido', ok: false })
    } finally {
      setScanning(false)
    }
  }

  async function handleClosePacking() {
    setActionLoading(true)
    setActionError(null)
    try {
      await api.post(`/fulfillment/orders/${id}/close-packing`)
      await loadPack()
      const o = await api.get<SalesOrder>(`/commercial/orders/${id}`)
      setOrder(o)
    } catch (err: any) {
      setActionError(err.detail ?? 'Error al cerrar packing')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleShip() {
    setActionLoading(true)
    setActionError(null)
    try {
      await api.post(`/fulfillment/orders/${id}/ship`)
      await loadPack()
      const o = await api.get<SalesOrder>(`/commercial/orders/${id}`)
      setOrder(o)
    } catch (err: any) {
      setActionError(err.detail ?? 'Error al enviar')
    } finally {
      setActionLoading(false)
    }
  }

  const allConfirmed =
    pack !== null &&
    pack.items.length > 0 &&
    pack.items.every((i) => i.confirmed_qty >= i.required_qty)

  const fulfillmentStatus = pack?.fulfillment_status ?? order?.fulfillment_status ?? 'PENDING'
  const isPacked = fulfillmentStatus === 'PACKED'
  const isShipped = fulfillmentStatus === 'SHIPPED'
  const isDelivered = fulfillmentStatus === 'DELIVERED'

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft size={14} /> Fulfillment
      </button>

      {/* Order header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">
            {order?.customer_name ?? 'Cargando…'}
          </h1>
          <p className="text-sm text-muted-foreground">{order?.customer_email}</p>
        </div>
        <Badge variant={(FULFILLMENT_VARIANT[fulfillmentStatus] ?? 'outline') as any}>
          {fulfillmentStatus}
        </Badge>
      </div>

      {/* Initialize packing */}
      {!pack || pack.items.length === 0 ? (
        <div className="rounded-lg border bg-muted/30 p-6 text-center space-y-3">
          <Package size={32} className="mx-auto text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Packing no inicializado</p>
          {order?.qr_token ? (
            <Button onClick={initPacking} disabled={actionLoading}>
              {actionLoading ? 'Inicializando…' : 'Inicializar packing'}
            </Button>
          ) : (
            <p className="text-xs text-muted-foreground">
              Esta orden no tiene QR token (¿está aprobada?)
            </p>
          )}
        </div>
      ) : (
        <>
          {/* Items progress */}
          <div className="space-y-3">
            <h2 className="text-base font-medium">
              Items ({pack.items.filter((i) => i.confirmed_qty >= i.required_qty).length}/{pack.items.length} listos)
            </h2>
            {pack.items.map((item) => (
              <ItemRow key={item.id} item={item} />
            ))}
          </div>

          {/* Scan kit QR */}
          {!isPacked && !isShipped && !isDelivered && (
            <div className="space-y-2">
              <h2 className="text-base font-medium flex items-center gap-2">
                <Scan size={16} />
                Escanear Kit
              </h2>
              <form onSubmit={handleScanKit} className="flex gap-2">
                <Input
                  placeholder="QR code del kit…"
                  value={kitQr}
                  onChange={(e) => {
                    setKitQr(e.target.value)
                    setScanMsg(null)
                  }}
                  className="font-mono text-xs"
                  autoFocus
                />
                <Button type="submit" disabled={scanning || !kitQr.trim()}>
                  {scanning ? '…' : 'Confirmar'}
                </Button>
              </form>
              {scanMsg && (
                <p className={`text-sm ${scanMsg.ok ? 'text-green-600' : 'text-destructive'}`}>
                  {scanMsg.text}
                </p>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            {!isPacked && !isShipped && !isDelivered && (
              <Button
                onClick={handleClosePacking}
                disabled={!allConfirmed || actionLoading}
                className="flex items-center gap-2"
              >
                <CheckCircle2 size={16} />
                {actionLoading ? 'Cerrando…' : 'Cerrar packing'}
              </Button>
            )}

            {isPacked && !isShipped && !isDelivered && (
              <Button
                onClick={handleShip}
                disabled={actionLoading}
                className="flex items-center gap-2"
              >
                <Send size={16} />
                {actionLoading ? 'Enviando…' : 'Enviar (ship)'}
              </Button>
            )}

            {(isShipped || isDelivered) && (
              <div className="flex items-center gap-2 text-green-600 text-sm font-medium">
                <CheckCircle2 size={16} />
                Orden {fulfillmentStatus.toLowerCase()}
              </div>
            )}
          </div>

          {actionError && (
            <p className="text-sm text-destructive">{actionError}</p>
          )}

          {/* Event log */}
          {pack.events.length > 0 && (
            <details className="text-sm">
              <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                Historial de eventos ({pack.events.length})
              </summary>
              <div className="mt-2 space-y-1 rounded-lg border bg-muted/30 p-3">
                {pack.events.map((ev) => (
                  <div key={ev.id} className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="font-mono">{new Date(ev.created_at).toLocaleTimeString('es-ES')}</span>
                    <Badge variant="outline" className="text-xs">{ev.event_type}</Badge>
                    {ev.quantity != null && <span>x{ev.quantity}</span>}
                    {ev.scanned_qr && <span className="font-mono">{ev.scanned_qr}</span>}
                  </div>
                ))}
              </div>
            </details>
          )}
        </>
      )}
    </div>
  )
}
