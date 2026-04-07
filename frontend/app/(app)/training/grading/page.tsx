'use client'

import { useEffect, useState } from 'react'
import {
  ClipboardList,
  Download,
  Eye,
  RefreshCw,
  X,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { TrainingProgram } from '@/lib/types'
import type {
  TrainingModule,
  TrainingEvaluation,
  TrainingSubmission,
} from '@/services/training'
import * as trainingService from '@/services/training'

export default function GradingPage() {
  const [programs, setPrograms] = useState<TrainingProgram[]>([])
  const [selectedProgramId, setSelectedProgramId] = useState<string | null>(null)
  const [modules, setModules] = useState<TrainingModule[]>([])
  const [practicalEvals, setPracticalEvals] = useState<TrainingEvaluation[]>([])
  const [selectedEvalId, setSelectedEvalId] = useState<string | null>(null)
  const [submissions, setSubmissions] = useState<TrainingSubmission[]>([])
  const [gradingSubmission, setGradingSubmission] = useState<TrainingSubmission | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingSubs, setLoadingSubs] = useState(false)

  // Load programs on mount
  useEffect(() => {
    trainingService.listPrograms()
      .then((p) => {
        setPrograms(p)
        if (p.length > 0) setSelectedProgramId(p[0].public_id)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  // Load modules + practical evals when program changes
  useEffect(() => {
    if (!selectedProgramId) return
    async function loadEvals() {
      const mods = await trainingService.listModules(selectedProgramId!)
      setModules(mods)
      const allPracticals: TrainingEvaluation[] = []
      for (const mod of mods) {
        const evals = await trainingService.listEvaluations(mod.public_id)
        allPracticals.push(...evals.filter((e) => e.type === 'PRACTICAL'))
      }
      setPracticalEvals(allPracticals)
      if (allPracticals.length > 0) {
        setSelectedEvalId(allPracticals[0].public_id)
      } else {
        setSelectedEvalId(null)
        setSubmissions([])
      }
    }
    loadEvals()
  }, [selectedProgramId])

  // Load submissions when eval changes
  useEffect(() => {
    if (!selectedEvalId) { setSubmissions([]); return }
    setLoadingSubs(true)
    trainingService.listSubmissions(selectedEvalId)
      .then(setSubmissions)
      .catch(() => setSubmissions([]))
      .finally(() => setLoadingSubs(false))
  }, [selectedEvalId])

  const selectedEval = practicalEvals.find((e) => e.public_id === selectedEvalId) ?? null
  const pendingCount = submissions.filter((s) => s.status === 'SUBMITTED').length

  function reloadSubmissions() {
    if (!selectedEvalId) return
    trainingService.listSubmissions(selectedEvalId).then(setSubmissions).catch(() => {})
  }

  function exportPending() {
    const pending = submissions.filter((s) => s.status === 'SUBMITTED')
    if (pending.length === 0) return
    const headers = ['ID', 'Fecha entrega', 'Estado', 'Contenido']
    const rows = pending.map((s) => [
      s.public_id,
      s.submitted_at ? new Date(s.submitted_at).toLocaleDateString('es-CO') : '',
      s.status,
      (s.content ?? '').replace(/,/g, ';').replace(/\n/g, ' '),
    ])
    const csv = [headers, ...rows].map((r) => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `pendientes-${selectedEval?.title ?? 'entregas'}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (loading) return <p className="py-12 text-center text-muted-foreground">Cargando…</p>

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-semibold">Entregas por Calificar</h1>
          {pendingCount > 0 && (
            <Badge variant="warning">{pendingCount} pendiente{pendingCount !== 1 && 's'}</Badge>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={reloadSubmissions}>
          <RefreshCw size={14} className="mr-1" /> Actualizar
        </Button>
      </div>

      {/* Program selector */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">Programa</label>
          <select
            className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
            value={selectedProgramId ?? ''}
            onChange={(e) => setSelectedProgramId(e.target.value)}
          >
            {programs.length === 0 && <option value="">Sin programas</option>}
            {programs.map((p) => (
              <option key={p.public_id} value={p.public_id}>{p.name}</option>
            ))}
          </select>
        </div>

        {/* Evaluation selector */}
        <div className="space-y-1">
          <label className="text-xs font-medium text-muted-foreground">Evaluación Práctica</label>
          <select
            className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
            value={selectedEvalId ?? ''}
            onChange={(e) => setSelectedEvalId(e.target.value)}
          >
            {practicalEvals.length === 0 && <option value="">Sin evaluaciones prácticas</option>}
            {practicalEvals.map((ev) => (
              <option key={ev.public_id} value={ev.public_id}>
                {ev.title} ({ev.passing_score}/{ev.max_score})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Eval info */}
      {selectedEval && (
        <div className="rounded-md border bg-muted/30 px-4 py-2 text-sm text-muted-foreground">
          <span className="font-medium text-foreground">{selectedEval.title}</span>
          {selectedEval.description && <span> — {selectedEval.description}</span>}
          <span className="ml-2">· Aprueba con {selectedEval.passing_score}/{selectedEval.max_score}</span>
        </div>
      )}

      {/* Actions bar */}
      {submissions.length > 0 && (
        <div className="flex justify-end">
          <Button variant="outline" size="sm" onClick={exportPending} disabled={pendingCount === 0}>
            <Download size={14} className="mr-1" /> Exportar pendientes ({pendingCount})
          </Button>
        </div>
      )}

      {/* Submissions table */}
      {loadingSubs && <p className="py-6 text-center text-sm text-muted-foreground">Cargando entregas…</p>}

      {!loadingSubs && selectedEvalId && submissions.length === 0 && (
        <p className="py-12 text-center text-muted-foreground">Sin entregas para esta evaluación</p>
      )}

      {!loadingSubs && submissions.length > 0 && (
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Entrega</th>
                <th className="px-4 py-3 text-center font-medium">Fecha</th>
                <th className="px-4 py-3 text-center font-medium">Estado</th>
                <th className="px-4 py-3 text-center font-medium">Score</th>
                <th className="px-4 py-3 text-center font-medium">Archivo</th>
                <th className="px-4 py-3 text-center font-medium">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {submissions.map((sub) => (
                <tr key={sub.public_id} className="border-b transition-colors hover:bg-muted/30">
                  <td className="px-4 py-3">
                    {sub.content ? (
                      <p className="max-w-[250px] text-xs text-muted-foreground line-clamp-2">{sub.content}</p>
                    ) : (
                      <span className="text-xs text-muted-foreground">Sin texto</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center text-xs text-muted-foreground">
                    {sub.submitted_at
                      ? new Date(sub.submitted_at).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })
                      : '—'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {sub.status === 'GRADED' && (
                      <Badge variant="success">Calificada</Badge>
                    )}
                    {sub.status === 'SUBMITTED' && (
                      <Badge variant="warning">Por calificar</Badge>
                    )}
                    {sub.status === 'PENDING' && (
                      <Badge variant="muted">Sin entregar</Badge>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {sub.score !== null && selectedEval ? (
                      <span className={`font-medium ${sub.score >= selectedEval.passing_score ? 'text-green-600' : 'text-red-600'}`}>
                        {sub.score}/{selectedEval.max_score}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {sub.file_name ? (
                      <span className="text-xs text-muted-foreground">{sub.file_name}</span>
                    ) : '—'}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {sub.status === 'SUBMITTED' && (
                      <Button size="sm" onClick={() => setGradingSubmission(sub)}>
                        Calificar
                      </Button>
                    )}
                    {sub.status === 'GRADED' && sub.feedback && (
                      <span className="text-xs text-muted-foreground" title={sub.feedback}>Feedback enviado</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Grade modal */}
      {gradingSubmission && selectedEval && (
        <GradeModal
          submission={gradingSubmission}
          evaluation={selectedEval}
          onClose={() => setGradingSubmission(null)}
          onGraded={() => {
            setGradingSubmission(null)
            reloadSubmissions()
          }}
        />
      )}
    </div>
  )
}

// ── Grade Modal ─────────────────────────────────────────────────────────────

function GradeModal({ submission, evaluation, onClose, onGraded }: {
  submission: TrainingSubmission
  evaluation: TrainingEvaluation
  onClose: () => void
  onGraded: () => void
}) {
  const [score, setScore] = useState('')
  const [feedback, setFeedback] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <div>
            <h3 className="font-semibold">Calificar entrega</h3>
            <p className="text-xs text-muted-foreground">{evaluation.title}</p>
          </div>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted"><X size={16} /></button>
        </div>
        <form
          onSubmit={async (e) => {
            e.preventDefault()
            setError(null)
            setSaving(true)
            try {
              await trainingService.gradeSubmission(submission.public_id, {
                score: parseInt(score, 10),
                feedback: feedback.trim() || null,
              })
              onGraded()
            } catch (err: any) {
              setError(err?.detail ?? 'Error al calificar')
            } finally {
              setSaving(false)
            }
          }}
          className="space-y-4 px-5 py-4"
        >
          {/* Submission content */}
          {submission.content && (
            <div className="space-y-1">
              <label className="text-xs font-medium">Respuesta del docente</label>
              <div className="max-h-40 overflow-y-auto rounded-md bg-muted/50 p-3 text-sm text-muted-foreground whitespace-pre-wrap">
                {submission.content}
              </div>
            </div>
          )}

          {/* Attached file */}
          {submission.file_name && (
            <div className="flex items-center gap-2 rounded-md bg-muted/30 px-3 py-2">
              <Eye size={14} className="text-muted-foreground" />
              <span className="text-sm text-muted-foreground">{submission.file_name}</span>
            </div>
          )}

          {/* Score */}
          <div className="space-y-1">
            <label className="text-xs font-medium">
              Puntaje (0–{evaluation.max_score}) *
            </label>
            <Input
              required
              type="number"
              min={0}
              max={evaluation.max_score}
              placeholder={`Máx. ${evaluation.max_score}`}
              value={score}
              onChange={(e) => setScore(e.target.value)}
            />
            <p className="text-[10px] text-muted-foreground">
              Aprueba con {evaluation.passing_score} pts
            </p>
          </div>

          {/* Feedback */}
          <div className="space-y-1">
            <label className="text-xs font-medium">Retroalimentación</label>
            <textarea
              className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Comentarios para el docente…"
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
            />
          </div>

          {error && (
            <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
          )}

          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" size="sm" disabled={saving}>
              {saving ? 'Guardando…' : 'Guardar calificación'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
