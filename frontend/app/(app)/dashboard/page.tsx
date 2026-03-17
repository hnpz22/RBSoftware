'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ShoppingCart, Factory, Package, TrendingUp, AlertTriangle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import type { SalesOrder, ProductionBatch, StockAlert } from '@/lib/types'

interface Stats {
  pendingOrders: number
  approvedOrders: number
  activeBatches: number
  criticalStock: number   // RED products
}

function StatCard({
  title,
  value,
  icon: Icon,
  sub,
  href,
  alert,
}: {
  title: string
  value: number | string
  icon: React.ElementType
  sub?: string
  href?: string
  alert?: boolean
}) {
  const content = (
    <Card className={alert && (value as number) > 0 ? 'border-red-200 bg-red-50/50 dark:border-red-900 dark:bg-red-950/20' : ''}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <Icon
          size={18}
          className={alert && (value as number) > 0 ? 'text-red-500' : 'text-muted-foreground'}
        />
      </CardHeader>
      <CardContent>
        <p className={`text-3xl font-bold ${alert && (value as number) > 0 ? 'text-red-600' : ''}`}>
          {value}
        </p>
        {sub && <p className="mt-1 text-xs text-muted-foreground">{sub}</p>}
        {href && (
          <p className="mt-2 text-xs text-primary underline-offset-2 hover:underline">
            Ver en inventario →
          </p>
        )}
      </CardContent>
    </Card>
  )

  if (href) {
    return <Link href={href}>{content}</Link>
  }
  return content
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [orders, batches, alerts] = await Promise.all([
          api.get<SalesOrder[]>('/commercial/orders'),
          api.get<ProductionBatch[]>('/production/batches'),
          api.get<StockAlert[]>('/inventory/alerts'),
        ])

        setStats({
          pendingOrders: orders.filter((o) => o.status === 'PENDING').length,
          approvedOrders: orders.filter((o) => o.status === 'APPROVED').length,
          activeBatches: batches.filter((b) =>
            ['PENDING', 'IN_PROGRESS'].includes(b.status),
          ).length,
          criticalStock: alerts.filter((a) => a.status_color === 'RED').length,
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
          title="Stock Crítico"
          value={stats?.criticalStock ?? 0}
          icon={AlertTriangle}
          sub="Productos sin unidades FREE"
          href="/inventory?color=RED"
          alert
        />
      </div>
    </div>
  )
}
