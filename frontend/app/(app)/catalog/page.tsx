'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ChevronRight, RefreshCw, Plus, X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ErrorBanner } from '@/components/error-banner'
import { Pagination } from '@/components/pagination'
import { useToast } from '@/components/ui/use-toast'
import { api } from '@/lib/api'
import type { Product } from '@/lib/types'

const ITEMS_PER_PAGE = 20

function ProductTypeBadge({ type }: { type: string }) {
  return (
    <Badge variant={type === 'KIT' ? 'default' : 'outline'}>
      {type}
    </Badge>
  )
}

interface CreateForm {
  sku: string
  name: string
  type: 'KIT' | 'COMPONENT'
  description: string
  cut_file_notes: string
}

const EMPTY_FORM: CreateForm = {
  sku: '',
  name: '',
  type: 'KIT',
  description: '',
  cut_file_notes: '',
}

export default function CatalogPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<CreateForm>(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const { toast } = useToast()

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const data = await api.get<Product[]>('/catalog/products?is_active=true')
      setProducts(data)
      setCurrentPage(1)
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar el catálogo. Verifica tu conexión.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      await api.post<Product>('/catalog/products', {
        sku: form.sku.trim(),
        name: form.name.trim(),
        type: form.type,
        description: form.description.trim() || null,
        cut_file_notes: form.type === 'COMPONENT' && form.cut_file_notes.trim()
          ? form.cut_file_notes.trim()
          : null,
      })
      setForm(EMPTY_FORM)
      setShowForm(false)
      toast({ title: 'Producto creado', variant: 'success' })
      await load()
    } catch (err: any) {
      toast({
        title: 'Error al crear el producto',
        description: err?.detail ?? 'Intenta de nuevo',
        variant: 'destructive',
      })
    } finally {
      setSaving(false)
    }
  }

  const totalPages = Math.ceil(products.length / ITEMS_PER_PAGE)
  const paginatedProducts = products.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE,
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Catálogo</h1>
          <p className="text-sm text-muted-foreground">{products.length} productos activos</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={load} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span className="ml-2 hidden sm:inline">Actualizar</span>
          </Button>
          <Button size="sm" onClick={() => setShowForm(true)}>
            <Plus size={14} className="mr-1" />
            <span className="hidden sm:inline">Nuevo producto</span>
          </Button>
        </div>
      </div>

      {error && <ErrorBanner message={error} onRetry={load} />}

      {/* Create form */}
      {showForm && (
        <div className="rounded-lg border bg-muted/30 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">Nuevo producto</p>
            <button onClick={() => { setShowForm(false); setForm(EMPTY_FORM) }}>
              <X size={16} className="text-muted-foreground hover:text-foreground" />
            </button>
          </div>
          <form onSubmit={handleCreate} className="space-y-3">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <label className="text-xs font-medium">SKU</label>
                <Input
                  placeholder="ej. KIT-EXPLORER-001"
                  value={form.sku}
                  onChange={(e) => setForm({ ...form, sku: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium">Tipo</label>
                <select
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                  value={form.type}
                  onChange={(e) => setForm({ ...form, type: e.target.value as 'KIT' | 'COMPONENT' })}
                >
                  <option value="KIT">KIT</option>
                  <option value="COMPONENT">COMPONENT</option>
                </select>
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">Nombre</label>
              <Input
                placeholder="ej. Kit Explorer Grado 3"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">Descripción (opcional)</label>
              <textarea
                className="w-full rounded-md border bg-background px-3 py-2 text-sm resize-none"
                rows={2}
                placeholder="Descripción del producto..."
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
              />
            </div>
            {form.type === 'COMPONENT' && (
              <div className="space-y-1">
                <label className="text-xs font-medium">Notas de archivo de corte (opcional)</label>
                <textarea
                  className="w-full rounded-md border bg-background px-3 py-2 text-sm resize-none"
                  rows={2}
                  placeholder="Ruta del archivo, versión, notas sobre el chasis..."
                  value={form.cut_file_notes}
                  onChange={(e) => setForm({ ...form, cut_file_notes: e.target.value })}
                />
              </div>
            )}
            <div className="flex gap-2">
              <Button type="submit" size="sm" disabled={saving}>
                {saving ? 'Creando…' : 'Crear producto'}
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => { setShowForm(false); setForm(EMPTY_FORM) }}
              >
                Cancelar
              </Button>
            </div>
          </form>
        </div>
      )}

      {/* Products table */}
      <div className="overflow-x-auto -mx-4 sm:mx-0 rounded-lg border">
        <div className="inline-block min-w-full align-middle px-4 sm:px-0">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="hidden px-4 py-3 text-left font-medium sm:table-cell">SKU</th>
                <th className="px-4 py-3 text-left font-medium">Nombre</th>
                <th className="px-4 py-3 text-left font-medium">Tipo</th>
                <th className="hidden px-4 py-3 text-left font-medium sm:table-cell">Activo</th>
                <th className="px-4 py-3 text-left font-medium" />
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                    Cargando…
                  </td>
                </tr>
              )}
              {!loading && !error && products.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                    No hay productos. Crea el primero con el botón de arriba.
                  </td>
                </tr>
              )}
              {paginatedProducts.map((p) => (
                <tr key={p.public_id} className="border-b last:border-0 hover:bg-muted/30">
                  <td className="hidden px-4 py-3 font-mono text-xs text-muted-foreground sm:table-cell">{p.sku}</td>
                  <td className="px-4 py-3 font-medium">{p.name}</td>
                  <td className="px-4 py-3">
                    <ProductTypeBadge type={p.type} />
                  </td>
                  <td className="hidden px-4 py-3 sm:table-cell">
                    <span className={p.is_active ? 'text-green-600' : 'text-muted-foreground'}>
                      {p.is_active ? 'Sí' : 'No'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Link href={`/catalog/${p.public_id}`}>
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
        totalItems={products.length}
        itemsPerPage={ITEMS_PER_PAGE}
      />
    </div>
  )
}
