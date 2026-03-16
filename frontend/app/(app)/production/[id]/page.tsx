'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, AlertTriangle } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api'
import type { MasterSheetResponse, MasterSheetItem } from '@/lib/types'

const STATUS_VARIANT: Record<string, string> = {
  PENDING: 'warning', IN_PROGRESS: 'info', DONE: 'success', CANCELLED: 'muted',
}

function BomRow({ item }: { item: MasterSheetItem }) {
  return (
    <div className="rounded-lg border p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <span className="font-mono text-sm font-medium">{item.product_sku}</span>
          <span className="ml-2 text-sm text-muted-foreground">{item.product_name}</span>
        </div>
        <div className="flex items-center gap-4 text-sm">
          <span className="text-muted-foreground">
            Requerido: <strong>{item.required_qty_total}</strong>
          </span>
          <span className="text-muted-foreground">
            Producir: <strong className={item.to_produce_qty > 0 ? 'text-amber-600' : ''}>{item.to_produce_qty}</strong>
          </span>
          <span className="text-muted-foreground">
            Producido: <strong className="text-green-600">{item.produced_qty}</strong>
          </span>
        </div>
      </div>

      {/* Blocks */}
      {item.blocks.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {item.blocks.map((block) => (
            <div
              key={block.id}
              className="flex items-center gap-1.5 rounded-md bg-destructive/10 px-2 py-1 text-xs text-destructive"
            >
              <AlertTriangle size={12} />
              Comp #{block.component_id} — faltan {block.missing_qty}
              {block.resolved_at && (
                <span className="ml-1 text-green-600">✓</span>
              )}
            </div>
          ))}
        </div>
      )}

      {/* BOM */}
      {item.bom.length > 0 && (
        <div>
          <p className="mb-2 text-xs font-medium text-muted-foreground uppercase tracking-wide">
            BOM
          </p>
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b">
                <th className="pb-1 text-left font-medium">Componente</th>
                <th className="pb-1 text-right font-medium">x Kit</th>
                <th className="pb-1 text-right font-medium">Total</th>
                <th className="pb-1 text-right font-medium">Disponible</th>
                <th className="pb-1 text-right font-medium">Falta</th>
              </tr>
            </thead>
            <tbody>
              {item.bom.map((b) => (
                <tr key={b.component_id} className="border-b last:border-0">
                  <td className="py-1">
                    <span className="font-mono">{b.component_sku}</span>
                    <span className="ml-1 text-muted-foreground">{b.component_name}</span>
                  </td>
                  <td className="py-1 text-right">{b.qty_per_kit}</td>
                  <td className="py-1 text-right">{b.total_needed}</td>
                  <td className="py-1 text-right text-green-600">{b.available}</td>
                  <td className={`py-1 text-right ${b.missing > 0 ? 'font-medium text-destructive' : 'text-muted-foreground'}`}>
                    {b.missing}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default function ProductionMasterSheetPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()
  const [sheet, setSheet] = useState<MasterSheetResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .get<MasterSheetResponse>(`/production/batches/${id}/master-sheet`)
      .then(setSheet)
      .catch((e) => setError(e.detail ?? 'Error al cargar'))
  }, [id])

  if (error) {
    return (
      <div className="space-y-4">
        <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft size={14} /> Volver
        </button>
        <p className="text-destructive">{error}</p>
      </div>
    )
  }

  if (!sheet) {
    return <p className="text-sm text-muted-foreground">Cargando hoja maestra…</p>
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <button onClick={() => router.back()} className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft size={14} /> Producción
      </button>

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">
            {sheet.name ?? 'Batch sin nombre'}
          </h1>
          <p className="text-sm text-muted-foreground font-mono">
            {sheet.batch_public_id.slice(0, 8)}… · {sheet.kind}
          </p>
        </div>
        <Badge variant={(STATUS_VARIANT[sheet.status] ?? 'outline') as any}>
          {sheet.status}
        </Badge>
      </div>

      {/* Linked orders */}
      {sheet.linked_orders.length > 0 && (
        <div className="text-sm">
          <span className="text-muted-foreground">Órdenes vinculadas: </span>
          {sheet.linked_orders.map((lo, i) => (
            <span key={lo.sales_order_id}>
              {i > 0 && ', '}
              <span className="font-mono">#{lo.sales_order_id}</span>
            </span>
          ))}
        </div>
      )}

      {/* Items */}
      <div className="space-y-4">
        <h2 className="text-base font-medium">
          Hoja Maestra — {sheet.items.length} producto{sheet.items.length !== 1 ? 's' : ''}
        </h2>
        {sheet.items.length === 0 && (
          <p className="text-sm text-muted-foreground">Sin items en este batch</p>
        )}
        {sheet.items.map((item) => (
          <BomRow key={item.batch_item_id} item={item} />
        ))}
      </div>
    </div>
  )
}
