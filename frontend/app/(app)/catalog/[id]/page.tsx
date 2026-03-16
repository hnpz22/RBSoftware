'use client'

import { useCallback, useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Plus, Trash2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { Product, KitBomItem } from '@/lib/types'

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>()
  const router = useRouter()

  const [product, setProduct] = useState<Product | null>(null)
  const [bom, setBom] = useState<KitBomItem[]>([])
  const [components, setComponents] = useState<Product[]>([])
  const [loadError, setLoadError] = useState<string | null>(null)

  // Add to BOM form
  const [showBomForm, setShowBomForm] = useState(false)
  const [selectedComponent, setSelectedComponent] = useState('')
  const [bomQty, setBomQty] = useState('1')
  const [bomNotes, setBomNotes] = useState('')
  const [bomSaving, setBomSaving] = useState(false)
  const [bomError, setBomError] = useState<string | null>(null)

  const loadBom = useCallback(async () => {
    try {
      const data = await api.get<KitBomItem[]>(`/catalog/products/${id}/bom`)
      setBom(data)
    } catch {
      // Not a kit or not found — bom stays empty
    }
  }, [id])

  useEffect(() => {
    api.get<Product>(`/catalog/products/${id}`)
      .then(setProduct)
      .catch(() => setLoadError('Producto no encontrado'))

    // Load components list for BOM add form
    api.get<Product[]>('/catalog/products?is_active=true')
      .then((all) => setComponents(all.filter((p) => p.type === 'COMPONENT')))
      .catch(() => {})

    loadBom()
  }, [id, loadBom])

  async function handleAddBom(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedComponent) return
    setBomError(null)
    setBomSaving(true)
    try {
      await api.post(`/catalog/products/${id}/bom`, {
        component_id: selectedComponent,
        quantity: parseInt(bomQty, 10),
        notes: bomNotes.trim() || null,
      })
      setSelectedComponent('')
      setBomQty('1')
      setBomNotes('')
      setShowBomForm(false)
      await loadBom()
    } catch (err: any) {
      setBomError(err.detail ?? 'Error al agregar componente')
    } finally {
      setBomSaving(false)
    }
  }

  async function handleRemoveBom(componentPublicId: string) {
    try {
      await api.delete(`/catalog/products/${id}/bom/${componentPublicId}`)
      await loadBom()
    } catch {
      // Silently reload
      await loadBom()
    }
  }

  if (loadError) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft size={14} /> Volver
        </button>
        <p className="text-destructive">{loadError}</p>
      </div>
    )
  }

  if (!product) {
    return <p className="text-sm text-muted-foreground">Cargando…</p>
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft size={14} /> Catálogo
      </button>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold">{product.name}</h1>
            <Badge variant={product.type === 'KIT' ? 'default' : 'outline'}>
              {product.type}
            </Badge>
          </div>
          <p className="font-mono text-sm text-muted-foreground">{product.sku}</p>
        </div>
        <span className={`text-sm ${product.is_active ? 'text-green-600' : 'text-muted-foreground'}`}>
          {product.is_active ? 'Activo' : 'Inactivo'}
        </span>
      </div>

      {/* Info */}
      {(product.description || product.cut_file_notes) && (
        <div className="space-y-2 text-sm">
          {product.description && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                Descripción
              </p>
              <p>{product.description}</p>
            </div>
          )}
          {product.cut_file_notes && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1">
                Notas de archivo de corte
              </p>
              <p className="rounded-md bg-muted/40 px-3 py-2 font-mono text-xs">
                {product.cut_file_notes}
              </p>
            </div>
          )}
        </div>
      )}

      {/* BOM — only for KITs */}
      {product.type === 'KIT' && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-medium">
              BOM — {bom.length} componente{bom.length !== 1 ? 's' : ''}
            </h2>
            <Button size="sm" onClick={() => { setShowBomForm(true); setBomError(null) }}>
              <Plus size={14} className="mr-1" />
              Agregar componente
            </Button>
          </div>

          {/* BOM add form */}
          {showBomForm && (
            <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
              <form onSubmit={handleAddBom} className="space-y-3">
                <div className="space-y-1">
                  <label className="text-xs font-medium">Componente</label>
                  <select
                    className="w-full rounded-md border bg-background px-3 py-2 text-sm"
                    value={selectedComponent}
                    onChange={(e) => setSelectedComponent(e.target.value)}
                    required
                  >
                    <option value="">— Seleccionar componente —</option>
                    {components
                      .filter((c) => !bom.some((b) => b.component_public_id === c.public_id))
                      .map((c) => (
                        <option key={c.public_id} value={c.public_id}>
                          {c.sku} — {c.name}
                        </option>
                      ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-xs font-medium">Cantidad por kit</label>
                    <Input
                      type="number"
                      min="1"
                      value={bomQty}
                      onChange={(e) => setBomQty(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium">Notas (opcional)</label>
                    <Input
                      placeholder="ej. bolsa 5g"
                      value={bomNotes}
                      onChange={(e) => setBomNotes(e.target.value)}
                    />
                  </div>
                </div>
                {bomError && (
                  <p className="text-sm text-destructive">{bomError}</p>
                )}
                <div className="flex gap-2">
                  <Button type="submit" size="sm" disabled={bomSaving || !selectedComponent}>
                    {bomSaving ? 'Agregando…' : 'Agregar'}
                  </Button>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => { setShowBomForm(false); setBomError(null) }}
                  >
                    Cancelar
                  </Button>
                </div>
              </form>
            </div>
          )}

          {/* BOM table */}
          <div className="rounded-lg border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-2 text-left font-medium">SKU</th>
                  <th className="px-4 py-2 text-left font-medium">Componente</th>
                  <th className="px-4 py-2 text-right font-medium">Cantidad</th>
                  <th className="px-4 py-2 text-left font-medium">Notas</th>
                  <th className="px-4 py-2" />
                </tr>
              </thead>
              <tbody>
                {bom.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-muted-foreground text-sm">
                      Sin componentes en el BOM. Agrega el primero.
                    </td>
                  </tr>
                )}
                {bom.map((item) => (
                  <tr key={item.component_public_id} className="border-b last:border-0">
                    <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                      {item.component_sku}
                    </td>
                    <td className="px-4 py-2">{item.component_name}</td>
                    <td className="px-4 py-2 text-right font-medium">{item.quantity}</td>
                    <td className="px-4 py-2 text-muted-foreground text-xs">
                      {item.notes ?? '—'}
                    </td>
                    <td className="px-4 py-2">
                      <button
                        onClick={() => handleRemoveBom(item.component_public_id)}
                        className="text-muted-foreground hover:text-destructive transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
