'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import {
  AlertTriangle,
  ChevronRight,
  LayoutGrid,
  List,
  Plus,
  Printer,
  RefreshCw,
  X,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { ProductionBatch, SalesOrder } from '@/lib/types'

// ── Helpers ───────────────────────────────────────────────────────────────────

const STATUS_VARIANT: Record<string, string> = {
  PENDING:     'warning',
  IN_PROGRESS: 'info',
  DONE:        'success',
  CANCELLED:   'muted',
}

const TRANSITIONS: Record<string, string[]> = {
  PENDING:     ['IN_PROGRESS', 'CANCELLED'],
  IN_PROGRESS: ['DONE', 'CANCELLED'],
}

const TRANSITION_LABEL: Record<string, string> = {
  IN_PROGRESS: 'Iniciar',
  DONE:        'Completar',
  CANCELLED:   'Cancelar',
}

const BATCH_KINDS = ['SALES', 'STOCK', 'FAIR', 'MANUAL'] as const
type BatchKind = (typeof BATCH_KINDS)[number]

// Kind badge colors (inline — avoids extending Badge variants)
const KIND_CLASS: Record<string, string> = {
  SALES:  'bg-blue-100   text-blue-700   dark:bg-blue-950   dark:text-blue-300',
  STOCK:  'bg-violet-100 text-violet-700 dark:bg-violet-950 dark:text-violet-300',
  FAIR:   'bg-amber-100  text-amber-700  dark:bg-amber-950  dark:text-amber-300',
  MANUAL: 'bg-slate-100  text-slate-600  dark:bg-slate-800  dark:text-slate-300',
}

// Kanban column definitions
const KANBAN_COLUMNS = [
  {
    status:    'PENDING',
    label:     'Pendiente',
    dotClass:  'bg-amber-400',
    colClass:  'bg-amber-50/70 dark:bg-amber-950/20',
  },
  {
    status:    'IN_PROGRESS',
    label:     'En Proceso',
    dotClass:  'bg-blue-400',
    colClass:  'bg-blue-50/70 dark:bg-blue-950/20',
  },
  {
    status:    'DONE',
    label:     'Completado',
    dotClass:  'bg-green-500',
    colClass:  'bg-green-50/70 dark:bg-green-950/20',
  },
] as const

// ── Cutoff Confirm Dialog ─────────────────────────────────────────────────────

function CutoffConfirmDialog({
  onClose,
  onConfirm,
  loading,
}: {
  onClose: () => void
  onConfirm: () => void
  loading: boolean
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-lg border bg-card p-6 shadow-xl">
        <div className="mb-4 flex items-start gap-3">
          <AlertTriangle size={20} className="mt-0.5 shrink-0 text-amber-500" />
          <div>
            <h3 className="font-semibold">Corte automático</h3>
            <p className="mt-1 text-sm text-muted-foreground">
              Esto agrupará todas las órdenes aprobadas pendientes en un batch de
              producción. ¿Continuar?
            </p>
          </div>
        </div>
        <div className="flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={loading}>
            Cancelar
          </Button>
          <Button size="sm" onClick={onConfirm} disabled={loading}>
            {loading ? 'Procesando…' : 'Confirmar'}
          </Button>
        </div>
      </div>
    </div>
  )
}

// ── New Batch Modal ───────────────────────────────────────────────────────────

function NewBatchModal({
  onClose,
  onCreated,
}: {
  onClose: () => void
  onCreated: () => void
}) {
  const [kind, setKind] = useState<BatchKind>('MANUAL')
  const [name, setName] = useState('')
  const [notes, setNotes] = useState('')
  const [approvedOrders, setApprovedOrders] = useState<SalesOrder[]>([])
  const [selectedOrderIds, setSelectedOrderIds] = useState<Set<string>>(new Set())
  const [loadingOrders, setLoadingOrders] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (kind !== 'SALES') {
      setApprovedOrders([])
      setSelectedOrderIds(new Set())
      return
    }
    setLoadingOrders(true)
    api
      .get<SalesOrder[]>('/commercial/orders')
      .then((orders) => setApprovedOrders(orders.filter((o) => o.status === 'APPROVED')))
      .catch(() => setApprovedOrders([]))
      .finally(() => setLoadingOrders(false))
  }, [kind])

  function toggleOrder(publicId: string) {
    setSelectedOrderIds((prev) => {
      const next = new Set(prev)
      next.has(publicId) ? next.delete(publicId) : next.add(publicId)
      return next
    })
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (kind === 'SALES' && selectedOrderIds.size === 0) {
      setError('Selecciona al menos una orden aprobada.')
      return
    }
    setSaving(true)
    try {
      await api.post('/production/batches', {
        kind,
        name: name.trim() || null,
        notes: notes.trim() || null,
        items: [],
        sales_order_public_ids: Array.from(selectedOrderIds),
      })
      onCreated()
    } catch (err: any) {
      setError(err?.detail ?? 'Error al crear el batch')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="relative max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">Nuevo batch de producción</h2>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 px-6 py-5">
          <div className="space-y-1">
            <label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Tipo
            </label>
            <div className="flex flex-wrap gap-2">
              {BATCH_KINDS.map((k) => (
                <button
                  key={k}
                  type="button"
                  onClick={() => setKind(k)}
                  className={`rounded-md border px-4 py-1.5 text-sm font-medium transition-colors ${
                    kind === k
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-input hover:bg-muted'
                  }`}
                >
                  {k}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Nombre <span className="normal-case text-muted-foreground/60">(opcional)</span>
            </label>
            <Input
              placeholder="Ej. Batch feria mayo"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Notas <span className="normal-case text-muted-foreground/60">(opcional)</span>
            </label>
            <textarea
              rows={2}
              placeholder="Observaciones internas..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {kind === 'SALES' && (
            <div className="space-y-2">
              <label className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Órdenes aprobadas
              </label>
              {loadingOrders && (
                <p className="text-sm text-muted-foreground">Cargando órdenes…</p>
              )}
              {!loadingOrders && approvedOrders.length === 0 && (
                <p className="rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground">
                  No hay órdenes aprobadas disponibles
                </p>
              )}
              {!loadingOrders && approvedOrders.length > 0 && (
                <div className="max-h-48 overflow-y-auto rounded-md border">
                  {approvedOrders.map((order) => {
                    const checked = selectedOrderIds.has(order.public_id)
                    return (
                      <label
                        key={order.public_id}
                        className={`flex cursor-pointer items-center gap-3 border-b px-3 py-2.5 last:border-0 hover:bg-muted/50 ${
                          checked ? 'bg-muted/40' : ''
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleOrder(order.public_id)}
                          className="h-4 w-4 rounded border-input accent-primary"
                        />
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium">{order.customer_name}</p>
                          <p className="truncate text-xs text-muted-foreground">
                            {order.customer_email} · {order.items.length} item
                            {order.items.length !== 1 ? 's' : ''}
                          </p>
                        </div>
                        <span className="shrink-0 text-xs text-muted-foreground">
                          {new Date(order.created_at).toLocaleDateString('es-ES')}
                        </span>
                      </label>
                    )
                  })}
                </div>
              )}
              {selectedOrderIds.size > 0 && (
                <p className="text-xs text-muted-foreground">
                  {selectedOrderIds.size} orden{selectedOrderIds.size !== 1 ? 'es' : ''}{' '}
                  seleccionada{selectedOrderIds.size !== 1 ? 's' : ''}
                </p>
              )}
            </div>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}

          <div className="flex justify-end gap-2 border-t pt-4">
            <Button type="button" variant="outline" onClick={onClose} disabled={saving}>
              Cancelar
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? 'Creando…' : 'Crear batch'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Kanban: BatchCard ─────────────────────────────────────────────────────────

function BatchCard({
  batch,
  updating,
  onUpdateStatus,
}: {
  batch: ProductionBatch
  updating: string | null
  onUpdateStatus: (publicId: string, newStatus: string) => void
}) {
  const nextSteps = TRANSITIONS[batch.status] ?? []

  return (
    <div className="rounded-lg border bg-card p-3.5 shadow-sm space-y-3">
      {/* Name + ID */}
      <div>
        <p className="font-medium leading-tight text-sm">
          {batch.name ?? (
            <span className="italic text-muted-foreground">Sin nombre</span>
          )}
        </p>
        <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
          {batch.public_id.slice(0, 8)}…
        </p>
      </div>

      {/* Kind + item count */}
      <div className="flex items-center justify-between gap-2">
        <span
          className={`rounded px-2 py-0.5 text-[11px] font-semibold ${
            KIND_CLASS[batch.kind] ?? 'bg-muted text-muted-foreground'
          }`}
        >
          {batch.kind}
        </span>
        <span className="text-xs text-muted-foreground">
          {batch.items.length} producto{batch.items.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Date */}
      <p className="text-xs text-muted-foreground">
        {new Date(batch.created_at).toLocaleDateString('es-ES')}
      </p>

      {/* Actions */}
      <div className="flex flex-wrap gap-1.5 border-t pt-2.5">
        <Link href={`/production/${batch.public_id}`}>
          <Button size="sm" variant="outline" className="h-7 px-2.5 text-xs">
            Ver
          </Button>
        </Link>
        {nextSteps
          .filter((s) => s !== 'CANCELLED')
          .map((s) => (
            <Button
              key={s}
              size="sm"
              className="h-7 px-2.5 text-xs"
              disabled={!!updating}
              onClick={() => onUpdateStatus(batch.public_id, s)}
            >
              {updating === batch.public_id + s ? '…' : TRANSITION_LABEL[s]}
            </Button>
          ))}
      </div>
    </div>
  )
}

// ── Kanban: Column ────────────────────────────────────────────────────────────

function KanbanColumn({
  column,
  batches,
  updating,
  onUpdateStatus,
}: {
  column: (typeof KANBAN_COLUMNS)[number]
  batches: ProductionBatch[]
  updating: string | null
  onUpdateStatus: (publicId: string, newStatus: string) => void
}) {
  const colBatches = batches.filter((b) => b.status === column.status)

  return (
    <div className={`flex flex-col rounded-xl p-3 ${column.colClass}`}>
      {/* Column header */}
      <div className="mb-3 flex items-center gap-2 px-1">
        <span className={`h-2 w-2 shrink-0 rounded-full ${column.dotClass}`} />
        <span className="text-sm font-semibold">{column.label}</span>
        <span className="ml-auto rounded-full bg-background/70 px-2 py-0.5 text-xs font-medium text-muted-foreground">
          {colBatches.length}
        </span>
      </div>

      {/* Cards */}
      <div className="flex flex-col gap-3">
        {colBatches.length === 0 ? (
          <p className="rounded-lg border border-dashed border-muted-foreground/30 py-10 text-center text-xs text-muted-foreground">
            Sin batches
          </p>
        ) : (
          colBatches.map((batch) => (
            <BatchCard
              key={batch.public_id}
              batch={batch}
              updating={updating}
              onUpdateStatus={onUpdateStatus}
            />
          ))
        )}
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

type View = 'list' | 'kanban'

export default function ProductionPage() {
  const [batches, setBatches] = useState<ProductionBatch[]>([])
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState<string | null>(null)
  const [printingId, setPrintingId] = useState<string | null>(null)
  const [showNewBatch, setShowNewBatch] = useState(false)
  const [showCutoffConfirm, setShowCutoffConfirm] = useState(false)
  const [cutoffLoading, setCutoffLoading] = useState(false)
  const [view, setView] = useState<View>('list')

  async function load() {
    setLoading(true)
    try {
      const data = await api.get<ProductionBatch[]>('/production/batches')
      setBatches(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function updateStatus(publicId: string, newStatus: string) {
    setUpdating(publicId + newStatus)
    try {
      await api.patch(`/production/batches/${publicId}/status`, { status: newStatus })
      await load()
    } catch {
      await load()
    } finally {
      setUpdating(null)
    }
  }

  async function handleCutoff() {
    setCutoffLoading(true)
    try {
      await api.post('/production/batches/cutoff')
      setShowCutoffConfirm(false)
      await load()
    } catch {
      await load()
    } finally {
      setCutoffLoading(false)
    }
  }

  async function openPdf(publicId: string) {
    setPrintingId(publicId)
    try {
      const res = await api.getRaw(`/production/batches/${publicId}/master-sheet/pdf`)
      if (!res.ok) throw new Error()
      const blob = await res.blob()
      window.open(URL.createObjectURL(blob), '_blank')
    } catch {
      // silently fail
    } finally {
      setPrintingId(null)
    }
  }

  function handleCreated() {
    setShowNewBatch(false)
    load()
  }

  return (
    <>
      {showNewBatch && (
        <NewBatchModal onClose={() => setShowNewBatch(false)} onCreated={handleCreated} />
      )}
      {showCutoffConfirm && (
        <CutoffConfirmDialog
          onClose={() => setShowCutoffConfirm(false)}
          onConfirm={handleCutoff}
          loading={cutoffLoading}
        />
      )}

      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Producción</h1>
            <p className="text-sm text-muted-foreground">{batches.length} batches</p>
          </div>
          <div className="flex items-center gap-2">
            {/* View toggle */}
            <div className="flex overflow-hidden rounded-md border">
              <button
                onClick={() => setView('list')}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium transition-colors ${
                  view === 'list'
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-muted'
                }`}
              >
                <List size={13} />
                Lista
              </button>
              <button
                onClick={() => setView('kanban')}
                className={`flex items-center gap-1.5 border-l px-3 py-1.5 text-xs font-medium transition-colors ${
                  view === 'kanban'
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-muted'
                }`}
              >
                <LayoutGrid size={13} />
                Kanban
              </button>
            </div>

            <Button variant="outline" size="sm" onClick={load} disabled={loading}>
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              <span className="ml-2">Actualizar</span>
            </Button>
            <Button variant="outline" size="sm" onClick={() => setShowCutoffConfirm(true)}>
              Corte automático
            </Button>
            <Button size="sm" onClick={() => setShowNewBatch(true)}>
              <Plus size={14} />
              <span className="ml-2">Nuevo batch</span>
            </Button>
          </div>
        </div>

        {/* ── LIST VIEW ── */}
        {view === 'list' && (
          <div className="rounded-lg border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium">Nombre</th>
                  <th className="px-4 py-3 text-left font-medium">Tipo</th>
                  <th className="px-4 py-3 text-left font-medium">Estado</th>
                  <th className="px-4 py-3 text-left font-medium">Items</th>
                  <th className="px-4 py-3 text-left font-medium">Acciones</th>
                  <th className="px-4 py-3 text-left font-medium" />
                </tr>
              </thead>
              <tbody>
                {loading && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                      Cargando…
                    </td>
                  </tr>
                )}
                {!loading && batches.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                      No hay batches de producción
                    </td>
                  </tr>
                )}
                {batches.map((batch) => {
                  const nextSteps = TRANSITIONS[batch.status] ?? []
                  return (
                    <tr key={batch.public_id} className="border-b last:border-0">
                      <td className="px-4 py-3">
                        <p className="font-medium">
                          {batch.name ?? (
                            <span className="italic text-muted-foreground">Sin nombre</span>
                          )}
                        </p>
                        <p className="font-mono text-xs text-muted-foreground">
                          {batch.public_id.slice(0, 8)}…
                        </p>
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded px-2 py-0.5 text-xs font-semibold ${
                            KIND_CLASS[batch.kind] ?? 'bg-muted text-muted-foreground'
                          }`}
                        >
                          {batch.kind}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={(STATUS_VARIANT[batch.status] ?? 'outline') as any}>
                          {batch.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {batch.items.length} producto{batch.items.length !== 1 ? 's' : ''}
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex gap-2">
                          {nextSteps.map((s) => (
                            <Button
                              key={s}
                              size="sm"
                              variant={s === 'CANCELLED' ? 'outline' : 'default'}
                              disabled={!!updating}
                              onClick={() => updateStatus(batch.public_id, s)}
                            >
                              {updating === batch.public_id + s ? '…' : TRANSITION_LABEL[s]}
                            </Button>
                          ))}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {batch.status === 'IN_PROGRESS' && (
                            <button
                              onClick={() => openPdf(batch.public_id)}
                              disabled={printingId === batch.public_id}
                              title="Imprimir hoja maestra"
                              className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-50"
                            >
                              <Printer size={15} />
                            </button>
                          )}
                          <Link href={`/production/${batch.public_id}`}>
                            <ChevronRight size={16} className="text-muted-foreground hover:text-foreground" />
                          </Link>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* ── KANBAN VIEW ── */}
        {view === 'kanban' && (
          <>
            {loading ? (
              <div className="grid grid-cols-3 gap-4">
                {KANBAN_COLUMNS.map((col) => (
                  <div
                    key={col.status}
                    className={`h-48 animate-pulse rounded-xl ${col.colClass}`}
                  />
                ))}
              </div>
            ) : (
              <div className="grid grid-cols-3 gap-4">
                {KANBAN_COLUMNS.map((col) => (
                  <KanbanColumn
                    key={col.status}
                    column={col}
                    batches={batches}
                    updating={updating}
                    onUpdateStatus={updateStatus}
                  />
                ))}
              </div>
            )}
            {!loading && batches.filter((b) => b.status === 'CANCELLED').length > 0 && (
              <p className="text-center text-xs text-muted-foreground">
                {batches.filter((b) => b.status === 'CANCELLED').length} batch
                {batches.filter((b) => b.status === 'CANCELLED').length !== 1 ? 'es' : ''}{' '}
                cancelado{batches.filter((b) => b.status === 'CANCELLED').length !== 1 ? 's' : ''}{' '}
                oculto{batches.filter((b) => b.status === 'CANCELLED').length !== 1 ? 's' : ''} — usa vista Lista para verlos.
              </p>
            )}
          </>
        )}
      </div>
    </>
  )
}
