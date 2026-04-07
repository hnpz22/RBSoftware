'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft,
  Award,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  ClipboardCheck,
  FileText,
  Send,
  Video,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import type { TrainingProgram, TeacherProgramProgress } from '@/lib/types'
import type {
  TrainingModule,
  TrainingLesson,
  TrainingEvaluation,
  QuizQuestion,
  TrainingSubmission,
} from '@/services/training'
import * as trainingService from '@/services/training'

interface Props {
  program: TrainingProgram
  modules: TrainingModule[]
  reload: () => void
}

export function TeacherProgramView({ program, modules }: Props) {
  const router = useRouter()
  const [progress, setProgress] = useState<TeacherProgramProgress | null>(null)

  useEffect(() => {
    trainingService.getMyPrograms().then((progs) => {
      const found = progs.find((p) => p.program_id === program.public_id)
      if (found) setProgress(found)
    }).catch(() => {})
  }, [program.public_id])

  const lessonPct = progress && progress.total_lessons > 0
    ? Math.round((progress.completed_lessons / progress.total_lessons) * 100) : 0

  const publishedModules = modules.filter((m) => m.is_published)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <button
          onClick={() => router.push('/training/my-programs')}
          className="mb-2 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft size={14} /> Mis Programas
        </button>
        <h1 className="text-2xl font-semibold">{program.name}</h1>
        {program.description && (
          <p className="mt-1 text-sm text-muted-foreground">{program.description}</p>
        )}
      </div>

      {/* Progress bar */}
      {progress && (
        <div className="space-y-1">
          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">Progreso general</span>
            <span className="font-medium">
              {progress.completed_lessons} de {progress.total_lessons} lecciones · {progress.passed_evaluations} de {progress.total_evaluations} evaluaciones
            </span>
          </div>
          <div className="h-2 rounded-full bg-muted">
            <div className="h-2 rounded-full bg-primary transition-all" style={{ width: `${lessonPct}%` }} />
          </div>
        </div>
      )}

      {publishedModules.length === 0 && (
        <p className="py-12 text-center text-muted-foreground">No hay contenido publicado</p>
      )}

      {/* Modules */}
      {publishedModules.map((mod) => (
        <TeacherModuleSection
          key={mod.public_id}
          module={mod}
          programId={program.public_id}
          onProgressChanged={() => {
            trainingService.getMyPrograms().then((progs) => {
              const found = progs.find((p) => p.program_id === program.public_id)
              if (found) setProgress(found)
            })
          }}
        />
      ))}

      {/* Certificate */}
      {progress?.is_certified && progress.certificate_code && (
        <div className="flex items-center gap-3 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/20">
          <Award size={24} className="text-green-600" />
          <div>
            <p className="font-medium text-green-700 dark:text-green-400">Certificado obtenido</p>
            <p className="text-sm text-green-600 dark:text-green-500">Código: {progress.certificate_code}</p>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Module section ──────────────────────────────────────────────────────────

function TeacherModuleSection({ module: mod, programId, onProgressChanged }: {
  module: TrainingModule; programId: string; onProgressChanged: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [lessons, setLessons] = useState<TrainingLesson[]>([])
  const [evaluations, setEvaluations] = useState<TrainingEvaluation[]>([])
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    if (expanded && !loaded) {
      Promise.all([
        trainingService.listLessons(mod.public_id),
        trainingService.listEvaluations(mod.public_id),
      ]).then(([l, e]) => {
        setLessons(l.filter((x) => x.is_published))
        setEvaluations(e.filter((x) => x.is_published))
        setLoaded(true)
      })
    }
  }, [expanded, loaded, mod.public_id])

  return (
    <div className="rounded-lg border">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-muted/30"
      >
        <div className="flex items-center gap-2">
          {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          <h2 className="font-medium">{mod.title}</h2>
        </div>
      </button>

      {expanded && (
        <div className="border-t px-4 py-3 space-y-4">
          {/* Lessons */}
          {lessons.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Lecciones ({lessons.length})
              </p>
              {lessons.map((l) => (
                <TeacherLessonItem key={l.public_id} lesson={l} onCompleted={onProgressChanged} />
              ))}
            </div>
          )}

          {/* Evaluations */}
          {evaluations.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Evaluaciones ({evaluations.length})
              </p>
              {evaluations.map((ev) => (
                <TeacherEvaluationItem key={ev.public_id} evaluation={ev} onSubmitted={onProgressChanged} />
              ))}
            </div>
          )}

          {lessons.length === 0 && evaluations.length === 0 && (
            <p className="text-sm text-muted-foreground">Sin contenido</p>
          )}
        </div>
      )}
    </div>
  )
}

// ── Lesson item ─────────────────────────────────────────────────────────────

function TeacherLessonItem({ lesson, onCompleted }: { lesson: TrainingLesson; onCompleted: () => void }) {
  const [completed, setCompleted] = useState(false)
  const [marking, setMarking] = useState(false)
  const [viewUrl, setViewUrl] = useState<string | null>(null)

  async function handleComplete() {
    setMarking(true)
    try {
      await trainingService.completeLesson(lesson.public_id)
      setCompleted(true)
      onCompleted()
    } catch {}
    finally { setMarking(false) }
  }

  async function handleView() {
    try {
      const data = await trainingService.getLessonViewUrl(lesson.public_id)
      window.open(data.url, '_blank')
    } catch {}
  }

  return (
    <div className="rounded-md border p-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {lesson.type === 'PDF' && <FileText size={16} className="text-red-500" />}
          {lesson.type === 'VIDEO' && <Video size={16} className="text-blue-500" />}
          {lesson.type === 'TEXT' && <BookOpen size={16} className="text-muted-foreground" />}
          <div>
            <p className="text-sm font-medium">{lesson.title}</p>
            <p className="text-xs text-muted-foreground">
              {lesson.type}{lesson.duration_minutes ? ` · ${lesson.duration_minutes} min` : ''}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {(lesson.type === 'PDF' || lesson.type === 'VIDEO') && lesson.file_key && (
            <Button variant="outline" size="sm" onClick={handleView}>Ver</Button>
          )}
          {completed ? (
            <span className="flex items-center gap-1 text-xs text-green-600"><CheckCircle2 size={14} /> Completada</span>
          ) : (
            <Button variant="outline" size="sm" disabled={marking} onClick={handleComplete}>
              <Check size={13} className="mr-1" /> {marking ? 'Marcando…' : 'Completar'}
            </Button>
          )}
        </div>
      </div>
      {lesson.type === 'TEXT' && lesson.content && (
        <div className="mt-2 rounded bg-muted/50 p-3 text-sm text-muted-foreground whitespace-pre-wrap">
          {lesson.content}
        </div>
      )}
    </div>
  )
}

// ── Evaluation item ─────────────────────────────────────────────────────────

function TeacherEvaluationItem({ evaluation, onSubmitted }: { evaluation: TrainingEvaluation; onSubmitted: () => void }) {
  const [submission, setSubmission] = useState<TrainingSubmission | null>(null)
  const [loadedSub, setLoadedSub] = useState(false)
  const [showQuiz, setShowQuiz] = useState(false)
  const [showPractical, setShowPractical] = useState(false)

  useEffect(() => {
    trainingService.getMySubmission(evaluation.public_id)
      .then((s) => { setSubmission(s); setLoadedSub(true) })
      .catch(() => setLoadedSub(true))
  }, [evaluation.public_id])

  const isGraded = submission?.status === 'GRADED'
  const passed = isGraded && submission.score !== null && submission.score >= evaluation.passing_score

  return (
    <div className="rounded-md border p-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ClipboardCheck size={16} className="text-muted-foreground" />
          <div>
            <p className="text-sm font-medium">{evaluation.title}</p>
            <p className="text-xs text-muted-foreground">
              {evaluation.type === 'QUIZ' ? 'Quiz' : 'Práctica'} · Aprueba con {evaluation.passing_score}/{evaluation.max_score}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isGraded && (
            <span className={`text-xs font-medium ${passed ? 'text-green-600' : 'text-red-600'}`}>
              {submission.score}/{evaluation.max_score} — {passed ? 'Aprobado' : 'No aprobado'}
            </span>
          )}
          {submission?.status === 'SUBMITTED' && (
            <span className="text-xs text-yellow-600">Pendiente de calificación</span>
          )}
          {!isGraded && evaluation.type === 'QUIZ' && (
            <Button size="sm" onClick={() => setShowQuiz(true)}>Hacer quiz</Button>
          )}
          {!isGraded && evaluation.type === 'PRACTICAL' && submission?.status !== 'SUBMITTED' && (
            <Button size="sm" onClick={() => setShowPractical(true)}>Entregar</Button>
          )}
        </div>
      </div>

      {/* Feedback */}
      {isGraded && submission.feedback && (
        <div className="mt-2 rounded bg-muted/50 p-2 text-sm text-muted-foreground">
          <span className="font-medium">Retroalimentación:</span> {submission.feedback}
        </div>
      )}

      {/* Quiz modal */}
      {showQuiz && (
        <QuizModal
          evaluationId={evaluation.public_id}
          passingScore={evaluation.passing_score}
          maxScore={evaluation.max_score}
          onClose={() => setShowQuiz(false)}
          onSubmitted={(sub) => { setSubmission(sub); setShowQuiz(false); onSubmitted() }}
        />
      )}

      {/* Practical modal */}
      {showPractical && (
        <PracticalModal
          evaluationId={evaluation.public_id}
          onClose={() => setShowPractical(false)}
          onSubmitted={(sub) => { setSubmission(sub); setShowPractical(false); onSubmitted() }}
        />
      )}
    </div>
  )
}

// ── Quiz Modal ──────────────────────────────────────────────────────────────

function QuizModal({ evaluationId, passingScore, maxScore, onClose, onSubmitted }: {
  evaluationId: string; passingScore: number; maxScore: number
  onClose: () => void; onSubmitted: (s: TrainingSubmission) => void
}) {
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [answers, setAnswers] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<TrainingSubmission | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    trainingService.listQuestions(evaluationId)
      .then((q) => { setQuestions(q); setLoading(false) })
      .catch(() => setLoading(false))
  }, [evaluationId])

  async function handleSubmit() {
    setError(null); setSubmitting(true)
    try {
      const sub = await trainingService.submitQuiz(evaluationId, answers)
      setResult(sub)
    } catch (err: any) { setError(err?.detail ?? 'Error al enviar') }
    finally { setSubmitting(false) }
  }

  const allAnswered = questions.every((q) => answers[q.public_id] !== undefined)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-2xl max-h-[80vh] overflow-y-auto rounded-lg border bg-card shadow-xl">
        <div className="sticky top-0 flex items-center justify-between border-b bg-card px-5 py-4">
          <h3 className="font-semibold">{result ? 'Resultado' : 'Quiz'}</h3>
          <button onClick={() => { if (result) onSubmitted(result); else onClose() }} className="rounded-md p-1 hover:bg-muted">
            <span className="sr-only">Cerrar</span>✕
          </button>
        </div>

        {loading && <p className="p-8 text-center text-muted-foreground">Cargando…</p>}

        {!loading && !result && (
          <div className="space-y-4 p-5">
            {questions.map((q, i) => (
              <div key={q.public_id} className="space-y-2">
                <p className="text-sm font-medium">{i + 1}. {q.question} <span className="text-xs text-muted-foreground">({q.points} pts)</span></p>
                <div className="space-y-1 pl-4">
                  {q.options.map((opt) => (
                    <label key={opt.id} className="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 text-sm hover:bg-muted/50">
                      <input
                        type="radio"
                        name={`q-${q.public_id}`}
                        checked={answers[q.public_id] === opt.id}
                        onChange={() => setAnswers({ ...answers, [q.public_id]: opt.id })}
                        className="accent-primary"
                      />
                      {opt.text}
                    </label>
                  ))}
                </div>
              </div>
            ))}
            {error && <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="outline" size="sm" onClick={onClose}>Cancelar</Button>
              <Button size="sm" disabled={!allAnswered || submitting} onClick={handleSubmit}>
                <Send size={13} className="mr-1" /> {submitting ? 'Enviando…' : 'Enviar respuestas'}
              </Button>
            </div>
          </div>
        )}

        {result && (
          <div className="p-5 text-center space-y-4">
            <div className={`text-5xl font-bold ${result.score !== null && result.score >= passingScore ? 'text-green-600' : 'text-red-600'}`}>
              {result.score}/{maxScore}
            </div>
            <p className={`text-lg font-medium ${result.score !== null && result.score >= passingScore ? 'text-green-600' : 'text-red-600'}`}>
              {result.score !== null && result.score >= passingScore ? '¡Aprobado!' : 'No aprobado'}
            </p>
            <p className="text-sm text-muted-foreground">Puntaje mínimo: {passingScore}</p>
            <Button onClick={() => onSubmitted(result)}>Cerrar</Button>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Practical Modal ─────────────────────────────────────────────────────────

function PracticalModal({ evaluationId, onClose, onSubmitted }: {
  evaluationId: string; onClose: () => void; onSubmitted: (s: TrainingSubmission) => void
}) {
  const [content, setContent] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setError(null); setSubmitting(true)
    try {
      const fd = new FormData()
      if (content.trim()) fd.append('content', content.trim())
      if (file) fd.append('file', file)
      const sub = await trainingService.submitPractical(evaluationId, fd)
      onSubmitted(sub)
    } catch (err: any) { setError(err?.detail ?? 'Error al entregar') }
    finally { setSubmitting(false) }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">Entregar evaluación práctica</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-3 px-5 py-4">
          <div className="space-y-1">
            <label className="text-xs font-medium">Respuesta</label>
            <textarea
              className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Escribe tu respuesta aquí…"
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium">Archivo adjunto</label>
            <input
              type="file"
              className="block w-full text-sm text-muted-foreground file:mr-2 file:rounded file:border-0 file:bg-muted file:px-3 file:py-1.5 file:text-sm file:font-medium"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
          {error && <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>Cancelar</Button>
            <Button type="submit" size="sm" disabled={submitting}>
              {submitting ? 'Entregando…' : 'Entregar'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
