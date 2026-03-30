'use client'

import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import * as academicService from '@/services/academic'
import type { User } from '@/lib/types'

interface Props {
  gradeId: string
  onClose: () => void
  onCreated: () => void
}

export function CreateCourseModal({ gradeId, onClose, onCreated }: Props) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [teacherId, setTeacherId] = useState('')
  const [users, setUsers] = useState<User[]>([])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    academicService.listUsers().then((all) => {
      setUsers(all.filter((u) => u.roles.includes('TEACHER')))
    })
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim() || !teacherId) return
    setSaving(true)
    setError(null)
    try {
      await academicService.createCourse(gradeId, {
        name: name.trim(),
        description: description.trim() || null,
        teacher_id: teacherId,
      })
      onCreated()
    } catch (err: any) {
      setError(err?.detail ?? 'Error al crear curso')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-background p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Nuevo Curso</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Nombre</label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ej: 4to B"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Descripción (opcional)</label>
            <Input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1">Docente</label>
            <select
              className="w-full rounded-md border bg-background px-3 py-2 text-sm"
              value={teacherId}
              onChange={(e) => setTeacherId(e.target.value)}
              required
            >
              <option value="">Seleccionar docente…</option>
              {users.map((u) => (
                <option key={u.public_id} value={u.public_id}>
                  {u.first_name} {u.last_name} — {u.email}
                </option>
              ))}
            </select>
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          <div className="flex justify-end gap-2">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" size="sm" disabled={saving || !name.trim() || !teacherId}>
              {saving ? 'Creando…' : 'Crear'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
