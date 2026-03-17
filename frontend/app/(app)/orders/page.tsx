'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ChevronRight, Plus, RefreshCw } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import type { SalesOrder } from '@/lib/types'

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

// ── Page ──────────────────────────────────────────────────────────────────────

export default function OrdersPage() {
  const [orders, setOrders] = useState<SalesOrder[]>([])
  const [loading, setLoading] = useState(true)

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

  return (
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
          <Button size="sm" asChild>
            <Link href="/orders/new">
              <Plus size={14} />
              <span className="ml-2">Nueva orden</span>
            </Link>
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
  )
}
