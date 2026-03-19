'use client'

import { useState } from 'react'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import * as academicService from '@/services/academic'

interface Props {
  schoolId: string
  onClose: () => void
  onCreated: () => void
}

export function CreateGradeModal({ schoolId, onClose, onCreated }: Props) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await academicService.createGrade(schoolId, {
        name: name.trim(),
        description: description.trim() || null,
      })
      onCreated()
    } catch (err: any) {
      setError(err?.detail ?? 'Error al crear el grado')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">Nuevo grado</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X size={16} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3 px-5 py-4">
          <div className="space-y-1">
            <label className="text-xs font-medium">Nombre *</label>
            <Input
              required
              placeholder="ej. 4to Primaria"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium">Descripción</label>
            <Input
              placeholder="Opcional"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          {error && (
            <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}
          <div className="flex justify-end gap-2 pt-1">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
            >
              Cancelar
            </Button>
            <Button type="submit" size="sm" disabled={saving}>
              {saving ? 'Creando…' : 'Crear grado'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
