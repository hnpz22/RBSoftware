'use client'

import { useState } from 'react'
import { ExternalLink, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import * as academicService from '@/services/academic'
import type { SubmissionWithStudent } from '@/lib/types'

interface Props {
  submission: SubmissionWithStudent
  onClose: () => void
  onGraded: () => void
}

export function GradeSubmissionModal({ submission, onClose, onGraded }: Props) {
  const [score, setScore] = useState('')
  const [feedback, setFeedback] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [downloadingFile, setDownloadingFile] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await academicService.gradeSubmission(submission.public_id, {
        score: parseInt(score),
        feedback: feedback.trim() || null,
      })
      onGraded()
    } catch (err: any) {
      setError(err?.detail ?? 'Error al calificar')
    } finally {
      setSaving(false)
    }
  }

  async function handleOpenFile() {
    setDownloadingFile(true)
    try {
      const { url } = await academicService.downloadSubmission(submission.public_id)
      window.open(url, '_blank')
    } finally {
      setDownloadingFile(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">
            Calificar — {submission.student.first_name}{' '}
            {submission.student.last_name}
          </h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X size={16} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3 px-5 py-4">
          {submission.content && (
            <div>
              <p className="text-xs font-medium text-muted-foreground mb-1">
                Respuesta:
              </p>
              <div className="rounded-md bg-muted/30 p-3 text-sm whitespace-pre-wrap">
                {submission.content}
              </div>
            </div>
          )}
          {submission.file_name && (
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">
                Archivo: {submission.file_name}
              </span>
              <Button
                type="button"
                size="sm"
                variant="outline"
                disabled={downloadingFile}
                onClick={handleOpenFile}
              >
                <ExternalLink size={12} />
                <span className="ml-1">
                  {downloadingFile ? 'Abriendo...' : 'Ver'}
                </span>
              </Button>
            </div>
          )}
          <div className="space-y-1">
            <label className="text-xs font-medium">Puntaje *</label>
            <Input
              required
              type="number"
              min="0"
              placeholder="0"
              value={score}
              onChange={(e) => setScore(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium">Retroalimentación</label>
            <textarea
              className="w-full min-h-[60px] rounded-md border border-input bg-background px-3 py-2 text-sm"
              placeholder="Comentarios…"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
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
              {saving ? 'Guardando…' : 'Calificar'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
