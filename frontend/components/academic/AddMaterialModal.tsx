'use client'

import { useState } from 'react'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import * as academicService from '@/services/academic'

interface Props {
  unitId: string
  onClose: () => void
  onCreated: () => void
}

const TYPES = ['PDF', 'VIDEO', 'LINK', 'TEXT'] as const

export function AddMaterialModal({ unitId, onClose, onCreated }: Props) {
  const [title, setTitle] = useState('')
  const [type, setType] = useState<string>('TEXT')
  const [content, setContent] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await academicService.addMaterial(
        unitId,
        {
          title: title.trim(),
          type,
          content:
            type === 'TEXT' || type === 'VIDEO' || type === 'LINK'
              ? content.trim() || null
              : null,
        },
        type === 'PDF' && file ? file : undefined,
      )
      onCreated()
    } catch (err: any) {
      setError(err?.detail ?? 'Error al agregar material')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">Agregar material</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X size={16} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3 px-5 py-4">
          <div className="space-y-1">
            <label className="text-xs font-medium">Tipo</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium">Título *</label>
            <Input
              required
              placeholder="Título del material"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          {type === 'PDF' && (
            <div className="space-y-1">
              <label className="text-xs font-medium">Archivo PDF</label>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                className="w-full text-sm"
              />
            </div>
          )}
          {(type === 'VIDEO' || type === 'LINK') && (
            <div className="space-y-1">
              <label className="text-xs font-medium">URL</label>
              <Input
                placeholder="https://..."
                value={content}
                onChange={(e) => setContent(e.target.value)}
              />
            </div>
          )}
          {type === 'TEXT' && (
            <div className="space-y-1">
              <label className="text-xs font-medium">Contenido</label>
              <textarea
                className="w-full min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="Escribe el contenido…"
                value={content}
                onChange={(e) => setContent(e.target.value)}
              />
            </div>
          )}
          {error && (
            <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" size="sm" disabled={saving}>
              {saving ? 'Guardando…' : 'Agregar'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
