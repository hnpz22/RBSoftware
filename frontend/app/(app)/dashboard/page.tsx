'use client'

import { useEffect, useState } from 'react'
import { ShoppingCart, Factory, Package, TrendingUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import type { SalesOrder, ProductionBatch, InventorySummaryItem } from '@/lib/types'

interface Stats {
  pendingOrders: number
  approvedOrders: number
  activeBatches: number
  stockEntries: number
}

function StatCard({
  title,
  value,
  icon: Icon,
  sub,
}: {
  title: string
  value: number | string
  icon: React.ElementType
  sub?: string
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon size={18} className="text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold">{value}</p>
        {sub && <p className="mt-1 text-xs text-muted-foreground">{sub}</p>}
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [orders, batches, summary] = await Promise.all([
          api.get<SalesOrder[]>('/commercial/orders'),
          api.get<ProductionBatch[]>('/production/batches'),
          api.get<InventorySummaryItem[]>('/inventory/balances/summary'),
        ])

        setStats({
          pendingOrders: orders.filter((o) => o.status === 'PENDING').length,
          approvedOrders: orders.filter((o) => o.status === 'APPROVED').length,
          activeBatches: batches.filter((b) =>
            ['PENDING', 'IN_PROGRESS'].includes(b.status),
          ).length,
          stockEntries: summary.filter((s) => s.status === 'FREE').length,
        })
      } catch {
        // show partial data or empty
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="h-10 animate-pulse rounded bg-muted" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">Resumen de operaciones</p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          title="Órdenes Pendientes"
          value={stats?.pendingOrders ?? 0}
          icon={ShoppingCart}
          sub="Por aprobar"
        />
        <StatCard
          title="Órdenes Aprobadas"
          value={stats?.approvedOrders ?? 0}
          icon={TrendingUp}
          sub="Listas para producción"
        />
        <StatCard
          title="Batches Activos"
          value={stats?.activeBatches ?? 0}
          icon={Factory}
          sub="En producción"
        />
        <StatCard
          title="Líneas de Stock Libre"
          value={stats?.stockEntries ?? 0}
          icon={Package}
          sub="Registros FREE en inventario"
        />
      </div>
    </div>
  )
}
