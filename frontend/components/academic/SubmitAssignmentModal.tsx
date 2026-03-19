'use client'

import { useState } from 'react'
import { X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import * as academicService from '@/services/academic'
import type { MySubmission, StudentAssignment } from '@/lib/types'

interface Props {
  assignment: StudentAssignment
  submission: MySubmission | null
  onClose: () => void
  onSubmitted: () => void
}

export function SubmitAssignmentModal({
  assignment,
  submission,
  onClose,
  onSubmitted,
}: Props) {
  const isGraded = submission?.status === 'GRADED'
  const [content, setContent] = useState(submission?.content ?? '')
  const [file, setFile] = useState<File | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await academicService.submitAssignment(
        assignment.public_id,
        content.trim() || null,
        file ?? undefined,
      )
      onSubmitted()
    } catch (err: any) {
      setError(err?.detail ?? 'Error al entregar')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">{assignment.title}</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-3 px-5 py-4">
          {assignment.description && (
            <p className="text-sm text-muted-foreground">
              {assignment.description}
            </p>
          )}

          {/* Existing submission info */}
          {submission && (
            <div className="rounded-md bg-muted/30 p-3 space-y-1">
              <p className="text-xs font-medium text-muted-foreground">
                Entrega actual — {submission.status}
              </p>
              {submission.submitted_at && (
                <p className="text-xs text-muted-foreground">
                  {new Date(submission.submitted_at).toLocaleString()}
                </p>
              )}
              {submission.file_name && (
                <p className="text-xs text-muted-foreground">
                  Archivo: {submission.file_name}
                </p>
              )}
            </div>
          )}

          {/* Graded feedback */}
          {isGraded && (
            <div className="rounded-md bg-green-500/10 p-3 space-y-1">
              <p className="text-sm font-medium text-green-700">
                Puntaje: {submission!.score}/{assignment.max_score}
              </p>
              {submission!.feedback && (
                <p className="text-sm text-green-700">
                  {submission!.feedback}
                </p>
              )}
            </div>
          )}

          {/* Form fields (only if not graded) */}
          {!isGraded && (
            <>
              <div className="space-y-1">
                <label className="text-xs font-medium">Respuesta</label>
                <textarea
                  className="w-full min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                  placeholder="Escribe tu respuesta…"
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-medium">
                  Archivo (opcional)
                </label>
                <input
                  type="file"
                  onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  className="w-full text-sm"
                />
              </div>
            </>
          )}

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
              {isGraded ? 'Cerrar' : 'Cancelar'}
            </Button>
            {!isGraded && (
              <Button type="submit" size="sm" disabled={saving}>
                {saving
                  ? 'Enviando…'
                  : submission
                    ? 'Actualizar entrega'
                    : 'Entregar'}
              </Button>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}
