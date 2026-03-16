'use client'

import { useEffect, useState } from 'react'
import { Plus, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import type { Permission, Role } from '@/lib/types'

// ── Small modal ────────────────────────────────────────────────────────────────

function Modal({
  title,
  onClose,
  children,
}: {
  title: string
  onClose: () => void
  children: React.ReactNode
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">{title}</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X size={16} />
          </button>
        </div>
        <div className="px-5 py-4">{children}</div>
      </div>
    </div>
  )
}

// ── Role detail panel ─────────────────────────────────────────────────────────

function RolePanel({
  role,
  allPermissions,
  onClose,
  onChanged,
}: {
  role: Role
  allPermissions: Permission[]
  onClose: () => void
  onChanged: () => void
}) {
  const [assigned, setAssigned] = useState<Permission[]>([])
  const [loading, setLoading] = useState(true)
  const [addingId, setAddingId] = useState('')
  const [busy, setBusy] = useState(false)

  async function loadPerms() {
    setLoading(true)
    try {
      const data = await api.get<Permission[]>(`/rbac/roles/${role.public_id}/permissions`)
      setAssigned(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadPerms() }, [role.public_id])

  const assignedIds = new Set(assigned.map((p) => p.public_id))
  const available = allPermissions.filter((p) => !assignedIds.has(p.public_id))

  async function handleAdd() {
    if (!addingId) return
    setBusy(true)
    try {
      await api.post(`/rbac/roles/${role.public_id}/permissions/${addingId}`)
      setAddingId('')
      await loadPerms()
      onChanged()
    } finally {
      setBusy(false)
    }
  }

  async function handleRemove(permPublicId: string) {
    setBusy(true)
    try {
      await api.delete(`/rbac/roles/${role.public_id}/permissions/${permPublicId}`)
      await loadPerms()
      onChanged()
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex w-80 shrink-0 flex-col border-l bg-card">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-4 py-3">
        <div className="min-w-0">
          <p className="truncate font-semibold">{role.name}</p>
          {role.description && (
            <p className="truncate text-xs text-muted-foreground">{role.description}</p>
          )}
        </div>
        <button onClick={onClose} className="ml-2 shrink-0 rounded-md p-1 hover:bg-muted">
          <X size={16} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Assigned permissions */}
        <div className="space-y-2">
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Permisos asignados
          </p>
          {loading && <p className="text-sm text-muted-foreground">Cargando…</p>}
          {!loading && assigned.length === 0 && (
            <p className="text-sm text-muted-foreground italic">Sin permisos asignados</p>
          )}
          {assigned.map((p) => (
            <div
              key={p.public_id}
              className="flex items-center justify-between gap-2 rounded-md border px-3 py-2"
            >
              <div className="min-w-0">
                <p className="truncate font-mono text-xs font-medium">{p.code}</p>
                {p.description && (
                  <p className="truncate text-xs text-muted-foreground">{p.description}</p>
                )}
              </div>
              <button
                onClick={() => handleRemove(p.public_id)}
                disabled={busy}
                className="shrink-0 text-muted-foreground hover:text-destructive disabled:opacity-50"
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>

        {/* Add permission */}
        {available.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Agregar permiso
            </p>
            <div className="flex gap-2">
              <select
                value={addingId}
                onChange={(e) => setAddingId(e.target.value)}
                className="flex-1 rounded-md border border-input bg-background px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              >
                <option value="">Seleccionar…</option>
                {available.map((p) => (
                  <option key={p.public_id} value={p.public_id}>
                    {p.code}
                  </option>
                ))}
              </select>
              <Button size="sm" onClick={handleAdd} disabled={!addingId || busy}>
                Agregar
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function RolesPage() {
  const [tab, setTab] = useState<'roles' | 'permissions'>('roles')
  const [roles, setRoles] = useState<Role[]>([])
  const [permissions, setPermissions] = useState<Permission[]>([])
  const [selectedRole, setSelectedRole] = useState<Role | null>(null)
  const [loading, setLoading] = useState(true)

  // New role modal
  const [showNewRole, setShowNewRole] = useState(false)
  const [roleName, setRoleName] = useState('')
  const [roleDesc, setRoleDesc] = useState('')
  const [roleError, setRoleError] = useState<string | null>(null)
  const [savingRole, setSavingRole] = useState(false)

  // New permission modal
  const [showNewPerm, setShowNewPerm] = useState(false)
  const [permCode, setPermCode] = useState('')
  const [permDesc, setPermDesc] = useState('')
  const [permError, setPermError] = useState<string | null>(null)
  const [savingPerm, setSavingPerm] = useState(false)

  async function loadRoles() {
    const data = await api.get<Role[]>('/rbac/roles')
    setRoles(data)
  }

  async function loadPermissions() {
    const data = await api.get<Permission[]>('/rbac/permissions')
    setPermissions(data)
  }

  async function loadAll() {
    setLoading(true)
    try {
      await Promise.all([loadRoles(), loadPermissions()])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadAll() }, [])

  async function handleCreateRole(e: React.FormEvent) {
    e.preventDefault()
    setRoleError(null)
    setSavingRole(true)
    try {
      await api.post('/rbac/roles', { name: roleName.trim(), description: roleDesc.trim() || null })
      setRoleName('')
      setRoleDesc('')
      setShowNewRole(false)
      await loadRoles()
    } catch (err: any) {
      setRoleError(err?.detail ?? 'Error al crear el rol')
    } finally {
      setSavingRole(false)
    }
  }

  async function handleCreatePermission(e: React.FormEvent) {
    e.preventDefault()
    setPermError(null)
    setSavingPerm(true)
    try {
      await api.post('/rbac/permissions', { code: permCode.trim(), description: permDesc.trim() || null })
      setPermCode('')
      setPermDesc('')
      setShowNewPerm(false)
      await loadPermissions()
    } catch (err: any) {
      setPermError(err?.detail ?? 'Error al crear el permiso')
    } finally {
      setSavingPerm(false)
    }
  }

  // Compute permission count per role (after panel changes)
  const [rolePermCounts, setRolePermCounts] = useState<Record<string, number>>({})

  function handleRolePermChanged() {
    // reload silently so counts stay fresh
    loadRoles()
  }

  return (
    <>
      {/* New Role Modal */}
      {showNewRole && (
        <Modal title="Nuevo rol" onClose={() => { setShowNewRole(false); setRoleError(null) }}>
          <form onSubmit={handleCreateRole} className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">Nombre</label>
              <Input
                required
                placeholder="ej. OPERATIVO"
                value={roleName}
                onChange={(e) => setRoleName(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">
                Descripción <span className="text-muted-foreground">(opcional)</span>
              </label>
              <Input
                placeholder="Descripción del rol"
                value={roleDesc}
                onChange={(e) => setRoleDesc(e.target.value)}
              />
            </div>
            {roleError && <p className="text-sm text-destructive">{roleError}</p>}
            <div className="flex justify-end gap-2 pt-1">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => { setShowNewRole(false); setRoleError(null) }}
              >
                Cancelar
              </Button>
              <Button type="submit" size="sm" disabled={savingRole}>
                {savingRole ? 'Creando…' : 'Crear'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* New Permission Modal */}
      {showNewPerm && (
        <Modal title="Nuevo permiso" onClose={() => { setShowNewPerm(false); setPermError(null) }}>
          <form onSubmit={handleCreatePermission} className="space-y-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">Código</label>
              <Input
                required
                placeholder="ej. commercial.sales_order.approve"
                value={permCode}
                onChange={(e) => setPermCode(e.target.value)}
                className="font-mono text-sm"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">
                Descripción <span className="text-muted-foreground">(opcional)</span>
              </label>
              <Input
                placeholder="Descripción del permiso"
                value={permDesc}
                onChange={(e) => setPermDesc(e.target.value)}
              />
            </div>
            {permError && <p className="text-sm text-destructive">{permError}</p>}
            <div className="flex justify-end gap-2 pt-1">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => { setShowNewPerm(false); setPermError(null) }}
              >
                Cancelar
              </Button>
              <Button type="submit" size="sm" disabled={savingPerm}>
                {savingPerm ? 'Creando…' : 'Crear'}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      <div className="flex h-full gap-0">
        {/* Main content */}
        <div className="flex-1 space-y-4 overflow-auto">
          {/* Header */}
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-semibold">Roles y Permisos</h1>
            <Button
              size="sm"
              onClick={() => tab === 'roles' ? setShowNewRole(true) : setShowNewPerm(true)}
            >
              <Plus size={14} />
              <span className="ml-2">{tab === 'roles' ? 'Nuevo rol' : 'Nuevo permiso'}</span>
            </Button>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 border-b">
            {(['roles', 'permissions'] as const).map((t) => (
              <button
                key={t}
                onClick={() => { setTab(t); setSelectedRole(null) }}
                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px ${
                  tab === t
                    ? 'border-primary text-foreground'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                {t === 'roles' ? 'Roles' : 'Permisos'}
              </button>
            ))}
          </div>

          {/* Tab: Roles */}
          {tab === 'roles' && (
            <div className="rounded-lg border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-3 text-left font-medium">Nombre</th>
                    <th className="px-4 py-3 text-left font-medium">Descripción</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && (
                    <tr>
                      <td colSpan={2} className="px-4 py-8 text-center text-muted-foreground">
                        Cargando…
                      </td>
                    </tr>
                  )}
                  {!loading && roles.length === 0 && (
                    <tr>
                      <td colSpan={2} className="px-4 py-8 text-center text-muted-foreground">
                        No hay roles
                      </td>
                    </tr>
                  )}
                  {roles.map((role) => (
                    <tr
                      key={role.public_id}
                      onClick={() => setSelectedRole(selectedRole?.public_id === role.public_id ? null : role)}
                      className={`cursor-pointer border-b last:border-0 hover:bg-muted/30 ${
                        selectedRole?.public_id === role.public_id ? 'bg-muted/40' : ''
                      }`}
                    >
                      <td className="px-4 py-3 font-medium">{role.name}</td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {role.description ?? <span className="italic text-xs">Sin descripción</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Tab: Permissions */}
          {tab === 'permissions' && (
            <div className="rounded-lg border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-3 text-left font-medium">Código</th>
                    <th className="px-4 py-3 text-left font-medium">Descripción</th>
                  </tr>
                </thead>
                <tbody>
                  {loading && (
                    <tr>
                      <td colSpan={2} className="px-4 py-8 text-center text-muted-foreground">
                        Cargando…
                      </td>
                    </tr>
                  )}
                  {!loading && permissions.length === 0 && (
                    <tr>
                      <td colSpan={2} className="px-4 py-8 text-center text-muted-foreground">
                        No hay permisos
                      </td>
                    </tr>
                  )}
                  {permissions.map((p) => (
                    <tr key={p.public_id} className="border-b last:border-0">
                      <td className="px-4 py-3 font-mono text-xs font-medium">{p.code}</td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {p.description ?? <span className="italic text-xs">Sin descripción</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Role detail panel */}
        {selectedRole && tab === 'roles' && (
          <RolePanel
            role={selectedRole}
            allPermissions={permissions}
            onClose={() => setSelectedRole(null)}
            onChanged={handleRolePermChanged}
          />
        )}
      </div>
    </>
  )
}
