'use client'

import { useState } from 'react'
import { Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import * as academicService from '@/services/academic'
import type { User } from '@/lib/types'

interface Props {
  courseId: string
  onClose: () => void
  onEnrolled: () => void
}

export function EnrollStudentModal({ courseId, onClose, onEnrolled }: Props) {
  const [email, setEmail] = useState('')
  const [results, setResults] = useState<User[]>([])
  const [searching, setSearching] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSearch() {
    if (!email.trim()) return
    setSearching(true)
    setError(null)
    try {
      const users = await academicService.listUsers()
      const filtered = users.filter(
        (u) =>
          u.email.toLowerCase().includes(email.toLowerCase()) && u.is_active,
      )
      setResults(filtered)
      if (filtered.length === 0) setError('No se encontraron usuarios')
    } catch {
      setError('Error al buscar')
    } finally {
      setSearching(false)
    }
  }

  async function handleEnroll(user: User) {
    setSaving(true)
    setError(null)
    try {
      await academicService.enrollStudent(courseId, user.public_id)
      onEnrolled()
    } catch (err: any) {
      setError(err?.detail ?? 'Error al matricular')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">Agregar estudiante</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X size={16} />
          </button>
        </div>
        <div className="space-y-3 px-5 py-4">
          <div className="flex gap-2">
            <Input
              placeholder="Buscar por email…"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button
              size="sm"
              variant="outline"
              onClick={handleSearch}
              disabled={searching}
            >
              <Search size={14} />
            </Button>
          </div>
          {error && (
            <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}
          {results.length > 0 && (
            <div className="max-h-48 space-y-1 overflow-y-auto">
              {results.map((u) => (
                <div
                  key={u.public_id}
                  className="flex items-center justify-between rounded-md border px-3 py-2"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">
                      {u.first_name} {u.last_name}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">
                      {u.email}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    disabled={saving}
                    onClick={() => handleEnroll(u)}
                  >
                    Matricular
                  </Button>
                </div>
              ))}
            </div>
          )}
          <div className="flex justify-end">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
            >
              Cerrar
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
