'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ChevronRight, RefreshCw } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { SalesOrder, PackStatusResponse } from '@/lib/types'

const FULFILLMENT_VARIANT: Record<string, string> = {
  PENDING: 'muted', IN_PROGRESS: 'info', PACKED: 'purple',
  SHIPPED: 'success', DELIVERED: 'success', CANCELLED: 'destructive',
}

export default function FulfillmentPage() {
  const [orders, setOrders] = useState<SalesOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [qrInput, setQrInput] = useState('')
  const [scanning, setScanning] = useState(false)
  const [scanError, setScanError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    try {
      const data = await api.get<SalesOrder[]>('/commercial/orders')
      // Show orders that are approved and not yet delivered/cancelled
      setOrders(
        data.filter((o) =>
          o.status === 'APPROVED' &&
          !['SHIPPED', 'DELIVERED', 'CANCELLED'].includes(o.fulfillment_status),
        ),
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleScanOrder(e: React.FormEvent) {
    e.preventDefault()
    if (!qrInput.trim()) return
    setScanError(null)
    setScanning(true)
    try {
      const data = await api.post<PackStatusResponse>('/fulfillment/scan/order', {
        qr_token: qrInput.trim(),
      })
      // Navigate to packing screen
      window.location.href = `/fulfillment/${data.order_public_id}`
    } catch (err: any) {
      setScanError(err.detail ?? 'QR no encontrado')
    } finally {
      setScanning(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Fulfillment</h1>
          <p className="text-sm text-muted-foreground">Órdenes aprobadas por empacar</p>
        </div>
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span className="ml-2">Actualizar</span>
        </Button>
      </div>

      {/* QR scan shortcut */}
      <div className="rounded-lg border bg-muted/30 p-4">
        <p className="mb-2 text-sm font-medium">Escanear QR de orden</p>
        <form onSubmit={handleScanOrder} className="flex gap-2">
          <Input
            placeholder="Pega o escanea el QR token aquí…"
            value={qrInput}
            onChange={(e) => setQrInput(e.target.value)}
            className="font-mono text-xs"
          />
          <Button type="submit" disabled={scanning || !qrInput.trim()}>
            {scanning ? '…' : 'Abrir'}
          </Button>
        </form>
        {scanError && <p className="mt-2 text-sm text-destructive">{scanError}</p>}
      </div>

      {/* Orders list */}
      <div className="rounded-lg border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left font-medium">Cliente</th>
              <th className="px-4 py-3 text-left font-medium">Fulfillment</th>
              <th className="px-4 py-3 text-left font-medium">Items</th>
              <th className="px-4 py-3 text-left font-medium" />
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                  Cargando…
                </td>
              </tr>
            )}
            {!loading && orders.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                  No hay órdenes por empacar
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
                  <Badge variant={(FULFILLMENT_VARIANT[order.fulfillment_status] ?? 'outline') as any}>
                    {order.fulfillment_status}
                  </Badge>
                </td>
                <td className="px-4 py-3 text-muted-foreground">{order.items.length}</td>
                <td className="px-4 py-3">
                  <Link href={`/fulfillment/${order.public_id}`}>
                    <ChevronRight size={16} className="text-muted-foreground hover:text-foreground" />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
