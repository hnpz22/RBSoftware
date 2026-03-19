'use client'

import { useState } from 'react'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import * as academicService from '@/services/academic'
import type { GradeCourseRow, GradeStudent } from '@/hooks/useGradeDetail'

interface Props {
  student: GradeStudent
  courses: GradeCourseRow[]
  onClose: () => void
  onTransferred: () => void
}

export function TransferStudentModal({
  student,
  courses,
  onClose,
  onTransferred,
}: Props) {
  const available = courses.filter((c) => c.public_id !== student.courseId)
  const [targetId, setTargetId] = useState(available[0]?.public_id ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!targetId) return
    setError(null)
    setSaving(true)
    try {
      await academicService.transferStudent(
        student.user.public_id,
        student.courseId,
        targetId,
      )
      onTransferred()
    } catch (err: any) {
      setError(err?.detail ?? 'Error al transferir')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">Transferir estudiante</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X size={16} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3 px-5 py-4">
          <p className="text-sm">
            <span className="font-medium">
              {student.user.first_name} {student.user.last_name}
            </span>
            <span className="text-muted-foreground">
              {' '}
              — actualmente en {student.courseName}
            </span>
          </p>
          <div className="space-y-1">
            <label className="text-xs font-medium">Curso destino</label>
            <select
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {available.map((c) => (
                <option key={c.public_id} value={c.public_id}>
                  {c.name}
                </option>
              ))}
            </select>
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
            <Button type="submit" size="sm" disabled={saving || !targetId}>
              {saving ? 'Transfiriendo…' : 'Transferir'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
