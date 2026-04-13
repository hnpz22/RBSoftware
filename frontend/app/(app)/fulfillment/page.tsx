'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ChevronRight, RefreshCw } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ErrorBanner } from '@/components/error-banner'
import { Pagination } from '@/components/pagination'
import { useToast } from '@/components/ui/use-toast'
import { api } from '@/lib/api'
import type { SalesOrder, PackStatusResponse } from '@/lib/types'

const ITEMS_PER_PAGE = 20

const FULFILLMENT_VARIANT: Record<string, string> = {
  PENDING: 'muted', IN_PROGRESS: 'info', PACKED: 'purple',
  SHIPPED: 'success', DELIVERED: 'success', CANCELLED: 'destructive',
}

export default function FulfillmentPage() {
  const [orders, setOrders] = useState<SalesOrder[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [qrInput, setQrInput] = useState('')
  const [scanning, setScanning] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const { toast } = useToast()

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<SalesOrder[]>('/commercial/orders')
      setOrders(
        data.filter((o) =>
          o.status === 'APPROVED' &&
          !['SHIPPED', 'DELIVERED', 'CANCELLED'].includes(o.fulfillment_status),
        ),
      )
      setCurrentPage(1)
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar fulfillment. Verifica tu conexión.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleScanOrder(e: React.FormEvent) {
    e.preventDefault()
    if (!qrInput.trim()) return
    setScanning(true)
    try {
      const data = await api.post<PackStatusResponse>('/fulfillment/scan/order', {
        qr_token: qrInput.trim(),
      })
      window.location.href = `/fulfillment/${data.order_public_id}`
    } catch (err: any) {
      toast({
        title: 'QR no encontrado',
        description: err?.detail ?? 'Verifica el código e intenta de nuevo',
        variant: 'destructive',
      })
    } finally {
      setScanning(false)
    }
  }

  const totalPages = Math.ceil(orders.length / ITEMS_PER_PAGE)
  const paginatedOrders = orders.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE,
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Fulfillment</h1>
          <p className="text-sm text-muted-foreground">Órdenes aprobadas por empacar</p>
        </div>
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span className="ml-2 hidden sm:inline">Actualizar</span>
        </Button>
      </div>

      {error && <ErrorBanner message={error} onRetry={load} />}

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
      </div>

      {/* Orders list */}
      <div className="overflow-x-auto -mx-4 sm:mx-0 rounded-lg border">
        <div className="inline-block min-w-full align-middle px-4 sm:px-0">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Cliente</th>
                <th className="px-4 py-3 text-left font-medium">Fulfillment</th>
                <th className="hidden px-4 py-3 text-left font-medium sm:table-cell">Items</th>
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
              {!loading && !error && orders.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                    No hay órdenes por empacar
                  </td>
                </tr>
              )}
              {paginatedOrders.map((order) => (
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
                  <td className="hidden px-4 py-3 text-muted-foreground sm:table-cell">{order.items.length}</td>
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

      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={setCurrentPage}
        totalItems={orders.length}
        itemsPerPage={ITEMS_PER_PAGE}
      />
    </div>
  )
}
