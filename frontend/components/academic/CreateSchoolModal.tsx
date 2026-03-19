'use client'

import { useState } from 'react'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import * as academicService from '@/services/academic'

interface Props {
  onClose: () => void
  onCreated: () => void
}

const EMPTY = {
  name: '',
  city: '',
  address: '',
  contact_name: '',
  contact_email: '',
  contact_phone: '',
}

export function CreateSchoolModal({ onClose, onCreated }: Props) {
  const [form, setForm] = useState(EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await academicService.createSchool({
        name: form.name.trim(),
        city: form.city.trim() || null,
        address: form.address.trim() || null,
        contact_name: form.contact_name.trim() || null,
        contact_email: form.contact_email.trim() || null,
        contact_phone: form.contact_phone.trim() || null,
      })
      onCreated()
    } catch (err: any) {
      setError(err?.detail ?? 'Error al crear el colegio')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">Nuevo colegio</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X size={16} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3 px-5 py-4">
          <div className="space-y-1">
            <label className="text-xs font-medium">Nombre *</label>
            <Input
              required
              placeholder="Nombre del colegio"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">Ciudad</label>
              <Input
                placeholder="Bogotá"
                value={form.city}
                onChange={(e) => setForm({ ...form, city: e.target.value })}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">Dirección</label>
              <Input
                placeholder="Calle 123 #45-67"
                value={form.address}
                onChange={(e) =>
                  setForm({ ...form, address: e.target.value })
                }
              />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">Nombre contacto</label>
              <Input
                placeholder="Juan Pérez"
                value={form.contact_name}
                onChange={(e) =>
                  setForm({ ...form, contact_name: e.target.value })
                }
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">Email contacto</label>
              <Input
                type="email"
                placeholder="contacto@colegio.edu"
                value={form.contact_email}
                onChange={(e) =>
                  setForm({ ...form, contact_email: e.target.value })
                }
              />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium">Teléfono contacto</label>
            <Input
              placeholder="+57 300 000 0000"
              value={form.contact_phone}
              onChange={(e) =>
                setForm({ ...form, contact_phone: e.target.value })
              }
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
              {saving ? 'Creando…' : 'Crear colegio'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
