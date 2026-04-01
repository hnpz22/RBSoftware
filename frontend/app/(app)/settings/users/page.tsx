'use client'

import { useEffect, useState } from 'react'
import { Plus, RefreshCw, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { Grade, Role, School, User } from '@/lib/types'

// ── Create user modal ─────────────────────────────────────────────────────────

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

function CreateUserModal({
  onClose,
  onCreated,
}: {
  onClose: () => void
  onCreated: () => void
}) {
  const [form, setForm] = useState<CreateUserForm>(EMPTY_FORM)
  const [roleId, setRoleId] = useState('')
  const [selectedRoleName, setSelectedRoleName] = useState('')
  const [roles, setRoles] = useState<Role[]>([])
  const [schools, setSchools] = useState<School[]>([])
  const [selectedSchoolId, setSelectedSchoolId] = useState('')
  const [grades, setGrades] = useState<Grade[]>([])
  const [selectedGradeId, setSelectedGradeId] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.get<Role[]>('/rbac/roles').then(setRoles)
    api.get<School[]>('/academic/schools').then(setSchools).catch(() => {})
  }, [])

  useEffect(() => {
    if (selectedRoleName === 'DIRECTOR' && selectedSchoolId) {
      api.get<Grade[]>(`/academic/schools/${selectedSchoolId}/grades`).then(setGrades).catch(() => {})
    } else {
      setGrades([])
      setSelectedGradeId('')
    }
  }, [selectedSchoolId, selectedRoleName])

  function handleRoleChange(value: string) {
    const role = roles.find((r) => r.public_id === value)
    setRoleId(value)
    setSelectedRoleName(role?.name ?? '')
    setSelectedSchoolId('')
    setSelectedGradeId('')
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!roleId) {
      setError('Selecciona un rol para el usuario')
      return
    }
    if (selectedRoleName === 'TEACHER' && !selectedSchoolId) {
      setError('Selecciona el colegio del docente')
      return
    }
    if (selectedRoleName === 'DIRECTOR' && !selectedSchoolId) {
      setError('Selecciona el colegio del director')
      return
    }
    if (selectedRoleName === 'DIRECTOR' && !selectedGradeId) {
      setError('Selecciona el grado a dirigir')
      return
    }
    setError(null)
    setSaving(true)
    try {
      const newUser = await api.post<User>('/auth/users', {
        email: form.email.trim(),
        password: form.password,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        phone: form.phone.trim() || null,
        position: form.position.trim() || null,
      })
      await api.post(`/rbac/users/${newUser.public_id}/roles/${roleId}`)

      if (selectedRoleName === 'TEACHER') {
        await api.post(`/academic/schools/${selectedSchoolId}/teachers`, {
          user_id: newUser.public_id,
        })
      }

      if (selectedRoleName === 'DIRECTOR') {
        await api.post(`/academic/grades/${selectedGradeId}/director`, {
          user_id: newUser.public_id,
        })
      }

      onCreated()
    } catch (err: any) {
      setError(err?.detail ?? 'Error al crear el usuario')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">Nuevo usuario</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X size={16} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3 px-5 py-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">Nombre</label>
              <Input required placeholder="Nombre" value={form.first_name}
                onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">Apellido</label>
              <Input required placeholder="Apellido" value={form.last_name}
                onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">Email</label>
              <Input required type="email" placeholder="usuario@robotschool.com" value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">Contraseña</label>
              <Input required type="password" placeholder="Mínimo 8 caracteres" value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">Teléfono (opcional)</label>
              <Input placeholder="+57 300 000 0000" value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">Cargo (opcional)</label>
              <Input placeholder="ej. Operario de bodega" value={form.position}
                onChange={(e) => setForm({ ...form, position: e.target.value })} />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium">Rol</label>
            <select
              required
              value={roleId}
              onChange={(e) => handleRoleChange(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">Seleccionar rol…</option>
              {roles.map((role) => (
                <option key={role.public_id} value={role.public_id}>
                  {role.name}{role.description ? ` — ${role.description}` : ''}
                </option>
              ))}
            </select>
          </div>

          {selectedRoleName === 'TEACHER' && (
            <div className="space-y-1">
              <label className="text-xs font-medium">
                Colegio<span className="text-destructive ml-1">*</span>
              </label>
              <select
                required
                value={selectedSchoolId}
                onChange={(e) => setSelectedSchoolId(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">Seleccionar colegio…</option>
                {schools.map((s) => (
                  <option key={s.public_id} value={s.public_id}>{s.name}</option>
                ))}
              </select>
            </div>
          )}

          {selectedRoleName === 'DIRECTOR' && (
            <>
              <div className="space-y-1">
                <label className="text-xs font-medium">
                  Colegio<span className="text-destructive ml-1">*</span>
                </label>
                <select
                  required
                  value={selectedSchoolId}
                  onChange={(e) => setSelectedSchoolId(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">Seleccionar colegio…</option>
                  {schools.map((s) => (
                    <option key={s.public_id} value={s.public_id}>{s.name}</option>
                  ))}
                </select>
              </div>
              {selectedSchoolId && (
                <div className="space-y-1">
                  <label className="text-xs font-medium">
                    Grado a dirigir<span className="text-destructive ml-1">*</span>
                  </label>
                  <select
                    required
                    value={selectedGradeId}
                    onChange={(e) => setSelectedGradeId(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    <option value="">Seleccionar grado…</option>
                    {grades.map((g) => (
                      <option key={g.public_id} value={g.public_id}>{g.name}</option>
                    ))}
                  </select>
                </div>
              )}
            </>
          )}

          {selectedRoleName === 'STUDENT' && (
            <p className="rounded-md bg-muted px-3 py-2 text-xs text-muted-foreground">
              Los estudiantes se matriculan directamente desde el curso en la sección Académico.
            </p>
          )}

          {error && (
            <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
          )}
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>Cancelar</Button>
            <Button type="submit" size="sm" disabled={saving}>
              {saving ? 'Creando…' : 'Crear usuario'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ── Change password modal ──────────────────────────────────────────────────────

function ChangePasswordModal({
  user,
  onClose,
}: {
  user: User
  onClose: () => void
}) {
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (newPassword.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres')
      return
    }
    if (newPassword !== confirmPassword) {
      setError('Las contraseñas no coinciden')
      return
    }
    setSaving(true)
    try {
      await api.patch(`/auth/users/${user.public_id}/password`, { new_password: newPassword })
      setSuccess(true)
      setTimeout(onClose, 1500)
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cambiar la contraseña')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">Cambiar contraseña</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X size={16} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3 px-5 py-4">
          {success ? (
            <p className="rounded-md bg-green-500/10 px-3 py-2 text-sm text-green-600">
              Contraseña actualizada
            </p>
          ) : (
            <>
              <div className="space-y-1">
                <label className="text-xs font-medium">Nueva contraseña</label>
                <Input
                  required
                  type="password"
                  placeholder="Mínimo 8 caracteres"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium">Confirmar contraseña</label>
                <Input
                  required
                  type="password"
                  placeholder="Repite la contraseña"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                />
              </div>
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
                  {saving ? 'Guardando…' : 'Guardar'}
                </Button>
              </div>
            </>
          )}
        </form>
      </div>
    </div>
  )
}

// ── User detail panel ─────────────────────────────────────────────────────────

function UserPanel({
  user,
  allRoles,
  onClose,
  onChanged,
}: {
  user: User
  allRoles: Role[]
  onClose: () => void
  onChanged: (updated?: User) => void
}) {
  const [userRoles, setUserRoles] = useState<Role[]>([])
  const [loadingRoles, setLoadingRoles] = useState(true)
  const [addingRoleId, setAddingRoleId] = useState('')
  const [busy, setBusy] = useState(false)
  const [showChangePwd, setShowChangePwd] = useState(false)

  // Edit form
  const [firstName, setFirstName] = useState(user.first_name)
  const [lastName, setLastName] = useState(user.last_name)
  const [phone, setPhone] = useState(user.phone ?? '')
  const [position, setPosition] = useState(user.position ?? '')
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)

  async function loadRoles() {
    setLoadingRoles(true)
    try {
      const data = await api.get<Role[]>(`/rbac/users/${user.public_id}/roles`)
      setUserRoles(data)
    } finally {
      setLoadingRoles(false)
    }
  }

  useEffect(() => { loadRoles() }, [user.public_id])

  const assignedRoleIds = new Set(userRoles.map((r) => r.public_id))
  const availableRoles = allRoles.filter((r) => !assignedRoleIds.has(r.public_id))

  async function handleSaveProfile(e: React.FormEvent) {
    e.preventDefault()
    setSaveError(null)
    setSaving(true)
    try {
      const updated = await api.patch<User>(`/auth/users/${user.public_id}`, {
        first_name: firstName.trim() || null,
        last_name: lastName.trim() || null,
        phone: phone.trim() || null,
        position: position.trim() || null,
      })
      onChanged(updated)
    } catch (err: any) {
      setSaveError(err?.detail ?? 'Error al guardar')
    } finally {
      setSaving(false)
    }
  }

  async function handleToggleActive() {
    setBusy(true)
    try {
      const updated = await api.patch<User>(`/auth/users/${user.public_id}`, {
        is_active: !user.is_active,
      })
      onChanged(updated)
    } catch {
      // no-op
    } finally {
      setBusy(false)
    }
  }

  async function handleAddRole() {
    if (!addingRoleId) return
    setBusy(true)
    try {
      await api.post(`/rbac/users/${user.public_id}/roles/${addingRoleId}`)
      setAddingRoleId('')
      await loadRoles()
      onChanged()
    } finally {
      setBusy(false)
    }
  }

  async function handleRemoveRole(rolePublicId: string) {
    setBusy(true)
    try {
      await api.delete(`/rbac/users/${user.public_id}/roles/${rolePublicId}`)
      await loadRoles()
      onChanged()
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
    {showChangePwd && (
      <ChangePasswordModal user={user} onClose={() => setShowChangePwd(false)} />
    )}
    <div className="flex w-80 shrink-0 flex-col border-l bg-card">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="min-w-0">
          <p className="truncate font-semibold">{user.first_name} {user.last_name}</p>
          <p className="truncate text-xs text-muted-foreground">{user.email}</p>
        </div>
        <button onClick={onClose} className="ml-2 shrink-0 rounded-md p-1 hover:bg-muted">
          <X size={16} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {/* Profile edit */}
        <form onSubmit={handleSaveProfile} className="space-y-3">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Datos del usuario
          </p>
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Nombre</label>
              <Input
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                className="h-8 text-sm"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-muted-foreground">Apellido</label>
              <Input
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                className="h-8 text-sm"
              />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Teléfono</label>
            <Input
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="—"
              className="h-8 text-sm"
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs text-muted-foreground">Cargo</label>
            <Input
              value={position}
              onChange={(e) => setPosition(e.target.value)}
              placeholder="—"
              className="h-8 text-sm"
            />
          </div>
          {saveError && <p className="text-xs text-destructive">{saveError}</p>}
          <Button type="submit" size="sm" className="w-full" disabled={saving}>
            {saving ? 'Guardando…' : 'Guardar cambios'}
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="w-full"
            onClick={() => setShowChangePwd(true)}
          >
            Cambiar contraseña
          </Button>
        </form>

        <hr />

        {/* Active toggle */}
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Estado
            </p>
            <p className={`mt-0.5 text-sm font-medium ${user.is_active ? 'text-green-600' : 'text-muted-foreground'}`}>
              {user.is_active ? 'Activo' : 'Inactivo'}
            </p>
          </div>
          <Button
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={handleToggleActive}
          >
            {user.is_active ? 'Desactivar' : 'Activar'}
          </Button>
        </div>

        <hr />

        {/* Roles */}
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Roles asignados
          </p>
          {loadingRoles && <p className="text-sm text-muted-foreground">Cargando…</p>}
          {!loadingRoles && userRoles.length === 0 && (
            <p className="text-sm italic text-muted-foreground">Sin roles</p>
          )}
          {userRoles.map((r) => (
            <div
              key={r.public_id}
              className="flex items-center justify-between gap-2 rounded-md border px-3 py-2"
            >
              <p className="text-sm font-medium">{r.name}</p>
              <button
                onClick={() => handleRemoveRole(r.public_id)}
                disabled={busy}
                className="text-muted-foreground hover:text-destructive disabled:opacity-50"
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>

        {availableRoles.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Asignar rol
            </p>
            <div className="flex gap-2">
              <select
                value={addingRoleId}
                onChange={(e) => setAddingRoleId(e.target.value)}
                className="flex-1 rounded-md border border-input bg-background px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">Seleccionar…</option>
                {availableRoles.map((r) => (
                  <option key={r.public_id} value={r.public_id}>
                    {r.name}
                  </option>
                ))}
              </select>
              <Button size="sm" onClick={handleAddRole} disabled={!addingRoleId || busy}>
                Asignar
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
    </>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function SettingsUsersPage() {
  const [users, setUsers] = useState<User[]>([])
  const [allRoles, setAllRoles] = useState<Role[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [showCreate, setShowCreate] = useState(false)

  async function load() {
    setLoading(true)
    try {
      const [usersData, rolesData] = await Promise.all([
        api.get<User[]>('/auth/users'),
        api.get<Role[]>('/rbac/roles'),
      ])
      setUsers(usersData)
      setAllRoles(rolesData)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  function handleUserChanged(updated?: User) {
    if (updated) {
      setUsers((prev) => prev.map((u) => (u.public_id === updated.public_id ? updated : u)))
      setSelectedUser(updated)
    }
    load()
  }

  function handleCreated() {
    setShowCreate(false)
    load()
  }

  return (
    <>
      {showCreate && (
        <CreateUserModal onClose={() => setShowCreate(false)} onCreated={handleCreated} />
      )}

      <div className="flex h-full gap-0">
        {/* Main content */}
        <div className="flex-1 space-y-4 overflow-auto">
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
              <Button size="sm" onClick={() => setShowCreate(true)}>
                <Plus size={14} />
                <span className="ml-2">Nuevo usuario</span>
              </Button>
            </div>
          </div>

          <div className="rounded-lg border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium">Nombre</th>
                  <th className="px-4 py-3 text-left font-medium">Email</th>
                  <th className="px-4 py-3 text-left font-medium">Cargo</th>
                  <th className="px-4 py-3 text-left font-medium">Roles</th>
                  <th className="px-4 py-3 text-left font-medium">Activo</th>
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
                {!loading && users.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">
                      No hay usuarios
                    </td>
                  </tr>
                )}
                {users.map((u) => (
                  <tr
                    key={u.public_id}
                    onClick={() =>
                      setSelectedUser(selectedUser?.public_id === u.public_id ? null : u)
                    }
                    className={`cursor-pointer border-b last:border-0 hover:bg-muted/30 ${
                      selectedUser?.public_id === u.public_id ? 'bg-muted/40' : ''
                    }`}
                  >
                    <td className="px-4 py-3 font-medium">
                      {u.first_name} {u.last_name}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{u.email}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {u.position ?? <span className="italic text-xs">Sin cargo</span>}
                    </td>
                    <td className="px-4 py-3">
                      {(u.roles ?? []).length === 0 ? (
                        <span className="italic text-xs text-muted-foreground">Sin roles</span>
                      ) : (
                        <div className="flex flex-wrap gap-1">
                          {(u.roles ?? []).map((name) => (
                            <span
                              key={name}
                              className="rounded-sm bg-muted px-1.5 py-0.5 text-[11px] font-medium"
                            >
                              {name}
                            </span>
                          ))}
                        </div>
                      )}
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

        {/* User detail panel */}
        {selectedUser && (
          <UserPanel
            user={selectedUser}
            allRoles={allRoles}
            onClose={() => setSelectedUser(null)}
            onChanged={handleUserChanged}
          />
        )}
      </div>
    </>
  )
}
