'use client'

import { useEffect, useState } from 'react'
import { RefreshCw, Plus, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { User } from '@/lib/types'

interface CreateUserForm {
  email: string
  password: string
  first_name: string
  last_name: string
  phone: string
  position: string
}

const EMPTY_FORM: CreateUserForm = {
  email: '',
  password: '',
  first_name: '',
  last_name: '',
  phone: '',
  position: '',
}

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<CreateUserForm>(EMPTY_FORM)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    try {
      const data = await api.get<User[]>('/auth/users')
      setUsers(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await api.post<User>('/auth/users', {
        email: form.email.trim(),
        password: form.password,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        phone: form.phone.trim() || null,
        position: form.position.trim() || null,
      })
      setForm(EMPTY_FORM)
      setShowForm(false)
      await load()
    } catch (err: any) {
      setError(err.detail ?? 'Error al crear el usuario')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Usuarios</h1>
          <p className="text-sm text-muted-foreground">{users.length} usuarios internos</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={load} disabled={loading}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span className="ml-2">Actualizar</span>
          </Button>
          <Button size="sm" onClick={() => { setShowForm(true); setError(null) }}>
            <Plus size={14} className="mr-1" />
            Nuevo usuario
          </Button>
        </div>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="rounded-lg border bg-muted/30 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">Nuevo usuario interno</p>
            <button
              onClick={() => { setShowForm(false); setError(null); setForm(EMPTY_FORM) }}
            >
              <X size={16} className="text-muted-foreground hover:text-foreground" />
            </button>
          </div>
          <form onSubmit={handleCreate} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-medium">Nombre</label>
                <Input
                  placeholder="Nombre"
                  value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium">Apellido</label>
                <Input
                  placeholder="Apellido"
                  value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                  required
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-medium">Email</label>
                <Input
                  type="email"
                  placeholder="usuario@robotschool.com"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium">Contraseña</label>
                <Input
                  type="password"
                  placeholder="Mínimo 8 caracteres"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-xs font-medium">Teléfono (opcional)</label>
                <Input
                  placeholder="+57 300 000 0000"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium">Cargo (opcional)</label>
                <Input
                  placeholder="ej. Operario de bodega"
                  value={form.position}
                  onChange={(e) => setForm({ ...form, position: e.target.value })}
                />
              </div>
            </div>
            {error && (
              <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {error}
              </p>
            )}
            <div className="flex gap-2">
              <Button type="submit" size="sm" disabled={saving}>
                {saving ? 'Creando…' : 'Crear usuario'}
              </Button>
              <Button
                type="button"
                size="sm"
                variant="outline"
                onClick={() => { setShowForm(false); setError(null); setForm(EMPTY_FORM) }}
              >
                Cancelar
              </Button>
            </div>
          </form>
        </div>
      )}

      {/* Users table */}
      <div className="rounded-lg border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="px-4 py-3 text-left font-medium">Nombre</th>
              <th className="px-4 py-3 text-left font-medium">Email</th>
              <th className="px-4 py-3 text-left font-medium">Cargo</th>
              <th className="px-4 py-3 text-left font-medium">Activo</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                  Cargando…
                </td>
              </tr>
            )}
            {!loading && users.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                  No hay usuarios
                </td>
              </tr>
            )}
            {users.map((u) => (
              <tr key={u.public_id} className="border-b last:border-0">
                <td className="px-4 py-3 font-medium">
                  {u.first_name} {u.last_name}
                </td>
                <td className="px-4 py-3 text-muted-foreground">{u.email}</td>
                <td className="px-4 py-3 text-muted-foreground">
                  {u.position ?? <span className="italic text-xs">Sin cargo</span>}
                </td>
                <td className="px-4 py-3">
                  <span className={u.is_active ? 'text-green-600' : 'text-muted-foreground'}>
                    {u.is_active ? 'Sí' : 'No'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
