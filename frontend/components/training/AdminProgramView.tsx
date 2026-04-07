'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  ClipboardCheck,
  FileText,
  Plus,
  Trash2,
  Video,
  X,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuthStore } from '@/lib/store'
import type { TrainingProgram, TrainingEnrollmentProgress } from '@/lib/types'
import type {
  TrainingModule,
  TrainingLesson,
  TrainingEvaluation,
  QuizQuestion,
} from '@/services/training'
import * as trainingService from '@/services/training'

interface Props {
  program: TrainingProgram
  modules: TrainingModule[]
  reload: () => void
}

type RightTab = 'lessons' | 'evaluations' | 'enrolled'

export function AdminProgramView({ program, modules, reload }: Props) {
  const router = useRouter()
  const { isAdmin } = useAuthStore()

  const [selectedModuleId, setSelectedModuleId] = useState<string | null>(
    modules[0]?.public_id ?? null,
  )
  const [rightTab, setRightTab] = useState<RightTab>('lessons')

  // Module content
  const [lessons, setLessons] = useState<TrainingLesson[]>([])
  const [evaluations, setEvaluations] = useState<TrainingEvaluation[]>([])
  const [questions, setQuestions] = useState<QuizQuestion[]>([])
  const [selectedEvalId, setSelectedEvalId] = useState<string | null>(null)
  const [enrolledProgress, setEnrolledProgress] = useState<TrainingEnrollmentProgress[]>([])

  // Modals
  const [showCreateModule, setShowCreateModule] = useState(false)
  const [showCreateLesson, setShowCreateLesson] = useState(false)
  const [showCreateEval, setShowCreateEval] = useState(false)
  const [showCreateQuestion, setShowCreateQuestion] = useState(false)
  const [showEnroll, setShowEnroll] = useState(false)

  const selectedModule = modules.find((m) => m.public_id === selectedModuleId) ?? null

  // Load module content on selection
  useEffect(() => {
    if (!selectedModuleId) return
    trainingService.listLessons(selectedModuleId).then(setLessons).catch(() => setLessons([]))
    trainingService.listEvaluations(selectedModuleId).then(setEvaluations).catch(() => setEvaluations([]))
    setSelectedEvalId(null)
    setQuestions([])
  }, [selectedModuleId])

  // Load questions when eval selected
  useEffect(() => {
    if (!selectedEvalId) { setQuestions([]); return }
    trainingService.listQuestions(selectedEvalId).then(setQuestions).catch(() => setQuestions([]))
  }, [selectedEvalId])

  // Load enrolled progress
  useEffect(() => {
    if (rightTab === 'enrolled') {
      trainingService.getProgramProgress(program.public_id).then(setEnrolledProgress).catch(() => setEnrolledProgress([]))
    }
  }, [rightTab, program.public_id])

  function reloadModuleContent() {
    if (!selectedModuleId) return
    trainingService.listLessons(selectedModuleId).then(setLessons).catch(() => {})
    trainingService.listEvaluations(selectedModuleId).then(setEvaluations).catch(() => {})
  }

  const tabs: { key: RightTab; label: string }[] = [
    { key: 'lessons', label: `Lecciones (${lessons.length})` },
    { key: 'evaluations', label: `Evaluaciones (${evaluations.length})` },
    { key: 'enrolled', label: 'Inscritos' },
  ]

  return (
    <>
      {/* ── Modals ── */}
      {showCreateModule && (
        <CreateModuleModal
          programId={program.public_id}
          orderIndex={modules.length}
          onClose={() => setShowCreateModule(false)}
          onCreated={() => { setShowCreateModule(false); reload() }}
        />
      )}
      {showCreateLesson && selectedModuleId && (
        <CreateLessonModal
          moduleId={selectedModuleId}
          onClose={() => setShowCreateLesson(false)}
          onCreated={() => { setShowCreateLesson(false); reloadModuleContent() }}
        />
      )}
      {showCreateEval && selectedModuleId && (
        <CreateEvaluationModal
          moduleId={selectedModuleId}
          onClose={() => setShowCreateEval(false)}
          onCreated={() => { setShowCreateEval(false); reloadModuleContent() }}
        />
      )}
      {showCreateQuestion && selectedEvalId && (
        <CreateQuestionModal
          evaluationId={selectedEvalId}
          onClose={() => setShowCreateQuestion(false)}
          onCreated={() => { setShowCreateQuestion(false); trainingService.listQuestions(selectedEvalId).then(setQuestions) }}
        />
      )}
      {showEnroll && (
        <EnrollTeacherModal
          programId={program.public_id}
          onClose={() => setShowEnroll(false)}
          onEnrolled={() => { setShowEnroll(false); trainingService.getProgramProgress(program.public_id).then(setEnrolledProgress) }}
        />
      )}

      <div className="flex h-full flex-col">
        {/* Header */}
        <div className="shrink-0 border-b px-4 py-3">
          <button
            onClick={() => router.push('/training/programs')}
            className="mb-1 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft size={12} /> Programas
          </button>
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-semibold">{program.name}</h1>
            <Badge variant={program.is_published ? 'success' : 'secondary'}>
              {program.is_published ? 'Publicado' : 'Borrador'}
            </Badge>
          </div>
          {program.description && (
            <p className="text-xs text-muted-foreground">{program.description}</p>
          )}
        </div>

        {/* Two-panel layout */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left panel — modules sidebar */}
          <div className="flex w-64 shrink-0 flex-col border-r bg-muted/20">
            <div className="flex items-center justify-between border-b px-3 py-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Módulos
              </p>
              <Button size="sm" variant="ghost" onClick={() => setShowCreateModule(true)}>
                <Plus size={14} />
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto">
              {modules.length === 0 && (
                <p className="px-3 py-6 text-center text-xs text-muted-foreground">Sin módulos</p>
              )}
              {modules.map((m) => (
                <button
                  key={m.public_id}
                  onClick={() => { setSelectedModuleId(m.public_id); setRightTab('lessons') }}
                  className={`w-full border-b px-3 py-3 text-left transition-colors ${
                    selectedModuleId === m.public_id
                      ? 'bg-primary/10 border-l-2 border-l-primary'
                      : 'hover:bg-muted/40'
                  }`}
                >
                  <p className="truncate text-sm font-medium">{m.title}</p>
                  <div className="mt-1 flex items-center gap-2">
                    <Badge variant={m.is_published ? 'success' : 'secondary'} className="text-[10px]">
                      {m.is_published ? 'Publicado' : 'Borrador'}
                    </Badge>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Right panel */}
          <div className="flex flex-1 flex-col overflow-hidden">
            {!selectedModule ? (
              <div className="flex flex-1 items-center justify-center text-muted-foreground">
                Selecciona un módulo
              </div>
            ) : (
              <>
                {/* Module header */}
                <div className="flex items-center justify-between border-b px-4 py-3">
                  <div>
                    <h2 className="font-medium">{selectedModule.title}</h2>
                    {selectedModule.description && (
                      <p className="text-xs text-muted-foreground">{selectedModule.description}</p>
                    )}
                  </div>
                  {!selectedModule.is_published && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={async () => {
                        await trainingService.publishModule(selectedModule.public_id)
                        reload()
                      }}
                    >
                      Publicar
                    </Button>
                  )}
                </div>

                {/* Tabs */}
                <div className="flex shrink-0 border-b px-4">
                  {tabs.map((t) => (
                    <button
                      key={t.key}
                      onClick={() => setRightTab(t.key)}
                      className={`px-4 py-2 text-sm font-medium border-b-2 ${
                        rightTab === t.key
                          ? 'border-primary text-foreground'
                          : 'border-transparent text-muted-foreground hover:text-foreground'
                      }`}
                    >
                      {t.label}
                    </button>
                  ))}
                </div>

                {/* Tab content */}
                <div className="flex-1 overflow-y-auto p-4">
                  {rightTab === 'lessons' && (
                    <div className="space-y-2">
                      <div className="flex justify-end">
                        <Button size="sm" onClick={() => setShowCreateLesson(true)}>
                          <Plus size={14} className="mr-1" /> Nueva lección
                        </Button>
                      </div>
                      {lessons.length === 0 && (
                        <p className="py-6 text-center text-sm text-muted-foreground">Sin lecciones</p>
                      )}
                      {lessons.map((l) => (
                        <div key={l.public_id} className="flex items-center justify-between rounded-lg border p-3">
                          <div className="flex items-center gap-3">
                            {l.type === 'PDF' && <FileText size={16} className="text-red-500" />}
                            {l.type === 'VIDEO' && <Video size={16} className="text-blue-500" />}
                            {l.type === 'TEXT' && <BookOpen size={16} className="text-muted-foreground" />}
                            <div>
                              <p className="text-sm font-medium">{l.title}</p>
                              <p className="text-xs text-muted-foreground">
                                {l.type}{l.duration_minutes ? ` · ${l.duration_minutes} min` : ''}
                              </p>
                            </div>
                          </div>
                          <Badge variant={l.is_published ? 'success' : 'secondary'} className="text-[10px]">
                            {l.is_published ? 'Publicada' : 'Borrador'}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  )}

                  {rightTab === 'evaluations' && (
                    <div className="space-y-2">
                      <div className="flex justify-end">
                        <Button size="sm" onClick={() => setShowCreateEval(true)}>
                          <Plus size={14} className="mr-1" /> Nueva evaluación
                        </Button>
                      </div>
                      {evaluations.length === 0 && (
                        <p className="py-6 text-center text-sm text-muted-foreground">Sin evaluaciones</p>
                      )}
                      {evaluations.map((ev) => (
                        <div key={ev.public_id}>
                          <div
                            onClick={() => setSelectedEvalId(selectedEvalId === ev.public_id ? null : ev.public_id)}
                            className={`flex cursor-pointer items-center justify-between rounded-lg border p-3 transition-colors hover:bg-muted/30 ${
                              selectedEvalId === ev.public_id ? 'border-primary bg-primary/5' : ''
                            }`}
                          >
                            <div className="flex items-center gap-3">
                              <ClipboardCheck size={16} className="text-muted-foreground" />
                              <div>
                                <p className="text-sm font-medium">{ev.title}</p>
                                <p className="text-xs text-muted-foreground">
                                  {ev.type === 'QUIZ' ? 'Quiz' : 'Práctica'} · Aprueba con {ev.passing_score}/{ev.max_score}
                                </p>
                              </div>
                            </div>
                            <Badge variant={ev.is_published ? 'success' : 'secondary'} className="text-[10px]">
                              {ev.is_published ? 'Publicada' : 'Borrador'}
                            </Badge>
                          </div>

                          {/* Questions panel for QUIZ */}
                          {selectedEvalId === ev.public_id && ev.type === 'QUIZ' && (
                            <div className="ml-6 mt-2 space-y-2 border-l-2 border-primary/20 pl-4">
                              <div className="flex items-center justify-between">
                                <p className="text-xs font-semibold uppercase text-muted-foreground">Preguntas ({questions.length})</p>
                                <Button size="sm" variant="outline" onClick={() => setShowCreateQuestion(true)}>
                                  <Plus size={12} className="mr-1" /> Pregunta
                                </Button>
                              </div>
                              {questions.map((q, i) => (
                                <div key={q.public_id} className="rounded-md border bg-card p-3">
                                  <div className="flex items-start justify-between">
                                    <p className="text-sm">
                                      <span className="font-medium text-muted-foreground">{i + 1}.</span>{' '}
                                      {q.question}
                                    </p>
                                    <button
                                      className="ml-2 shrink-0 rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                                      onClick={async () => {
                                        await trainingService.deleteQuestion(q.public_id)
                                        trainingService.listQuestions(ev.public_id).then(setQuestions)
                                      }}
                                    >
                                      <Trash2 size={13} />
                                    </button>
                                  </div>
                                  <div className="mt-2 grid grid-cols-2 gap-1">
                                    {q.options.map((opt) => (
                                      <div
                                        key={opt.id}
                                        className={`rounded px-2 py-1 text-xs ${
                                          opt.id === q.correct_option
                                            ? 'bg-green-100 font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                            : 'bg-muted text-muted-foreground'
                                        }`}
                                      >
                                        {opt.text}
                                      </div>
                                    ))}
                                  </div>
                                  <p className="mt-1 text-[10px] text-muted-foreground">{q.points} pts</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {rightTab === 'enrolled' && (
                    <div className="space-y-3">
                      {isAdmin() && (
                        <div className="flex justify-end">
                          <Button size="sm" onClick={() => setShowEnroll(true)}>
                            <Plus size={14} className="mr-1" /> Inscribir docente
                          </Button>
                        </div>
                      )}
                      {enrolledProgress.length === 0 && (
                        <p className="py-6 text-center text-sm text-muted-foreground">Sin inscritos</p>
                      )}
                      {enrolledProgress.map((ep) => {
                        const lessonPct = ep.lessons_total > 0 ? Math.round((ep.lessons_completed / ep.lessons_total) * 100) : 0
                        return (
                          <div key={ep.enrollment_public_id} className="rounded-lg border p-4">
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="text-sm font-medium">{ep.user.first_name} {ep.user.last_name}</p>
                                <p className="text-xs text-muted-foreground">{ep.user.email}</p>
                              </div>
                              <div className="flex items-center gap-2">
                                {ep.is_eligible && !ep.status?.includes('COMPLETED') && isAdmin() && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={async () => {
                                      try {
                                        await trainingService.issueCertificate(ep.enrollment_public_id)
                                        trainingService.getProgramProgress(program.public_id).then(setEnrolledProgress)
                                      } catch {}
                                    }}
                                  >
                                    <CheckCircle2 size={13} className="mr-1" /> Emitir certificado
                                  </Button>
                                )}
                                <Badge variant={ep.status === 'COMPLETED' ? 'success' : 'secondary'}>
                                  {ep.status === 'COMPLETED' ? 'Completado' : 'Activo'}
                                </Badge>
                              </div>
                            </div>
                            <div className="mt-3">
                              <div className="mb-1 flex justify-between text-xs text-muted-foreground">
                                <span>Lecciones {ep.lessons_completed}/{ep.lessons_total}</span>
                                <span>Evaluaciones {ep.evaluations_passed}/{ep.evaluations_total}</span>
                              </div>
                              <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                                <div className="h-full rounded-full bg-blue-600 transition-all" style={{ width: `${lessonPct}%` }} />
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

// ── Inline Modals ───────────────────────────────────────────────────────────

function CreateModuleModal({ programId, orderIndex, onClose, onCreated }: {
  programId: string; orderIndex: number; onClose: () => void; onCreated: () => void
}) {
  const [title, setTitle] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">Nuevo módulo</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted"><X size={16} /></button>
        </div>
        <form onSubmit={async (e) => {
          e.preventDefault(); setError(null); setSaving(true)
          try { await trainingService.createModule(programId, { title: title.trim(), order_index: orderIndex }); onCreated() }
          catch (err: any) { setError(err?.detail ?? 'Error') }
          finally { setSaving(false) }
        }} className="space-y-3 px-5 py-4">
          <div className="space-y-1">
            <label className="text-xs font-medium">Título *</label>
            <Input required placeholder="Nombre del módulo" value={title} onChange={(e) => setTitle(e.target.value)} />
          </div>
          {error && <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>Cancelar</Button>
            <Button type="submit" size="sm" disabled={saving}>{saving ? 'Creando…' : 'Crear'}</Button>
          </div>
        </form>
      </div>
    </div>
  )
}

function CreateLessonModal({ moduleId, onClose, onCreated }: {
  moduleId: string; onClose: () => void; onCreated: () => void
}) {
  const [form, setForm] = useState({ title: '', type: 'TEXT', content: '', duration_minutes: '' })
  const [file, setFile] = useState<File | null>(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">Nueva lección</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted"><X size={16} /></button>
        </div>
        <form onSubmit={async (e) => {
          e.preventDefault(); setError(null); setSaving(true)
          try {
            const fd = new FormData()
            fd.append('title', form.title.trim())
            fd.append('type', form.type)
            if (form.content.trim()) fd.append('content', form.content.trim())
            if (form.duration_minutes) fd.append('duration_minutes', form.duration_minutes)
            if (file) fd.append('file', file)
            await trainingService.createLesson(moduleId, fd)
            onCreated()
          } catch (err: any) { setError(err?.detail ?? 'Error') }
          finally { setSaving(false) }
        }} className="space-y-3 px-5 py-4">
          <div className="space-y-1">
            <label className="text-xs font-medium">Título *</label>
            <Input required placeholder="Título de la lección" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">Tipo *</label>
              <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
                <option value="TEXT">Texto</option>
                <option value="PDF">PDF</option>
                <option value="VIDEO">Video</option>
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">Duración (min)</label>
              <Input type="number" min={1} placeholder="30" value={form.duration_minutes} onChange={(e) => setForm({ ...form, duration_minutes: e.target.value })} />
            </div>
          </div>
          {form.type === 'TEXT' && (
            <div className="space-y-1">
              <label className="text-xs font-medium">Contenido</label>
              <textarea className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" placeholder="Contenido de la lección" value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} />
            </div>
          )}
          {(form.type === 'PDF' || form.type === 'VIDEO') && (
            <div className="space-y-1">
              <label className="text-xs font-medium">Archivo</label>
              <input type="file" accept={form.type === 'PDF' ? '.pdf' : 'video/*'} className="block w-full text-sm text-muted-foreground file:mr-2 file:rounded file:border-0 file:bg-muted file:px-3 file:py-1.5 file:text-sm file:font-medium" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
            </div>
          )}
          {error && <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>Cancelar</Button>
            <Button type="submit" size="sm" disabled={saving}>{saving ? 'Creando…' : 'Crear lección'}</Button>
          </div>
        </form>
      </div>
    </div>
  )
}

function CreateEvaluationModal({ moduleId, onClose, onCreated }: {
  moduleId: string; onClose: () => void; onCreated: () => void
}) {
  const [form, setForm] = useState({ title: '', type: 'QUIZ', description: '', max_score: '100', passing_score: '60' })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">Nueva evaluación</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted"><X size={16} /></button>
        </div>
        <form onSubmit={async (e) => {
          e.preventDefault(); setError(null); setSaving(true)
          try {
            await trainingService.createEvaluation(moduleId, {
              title: form.title.trim(), type: form.type,
              description: form.description.trim() || undefined,
              max_score: parseInt(form.max_score, 10), passing_score: parseInt(form.passing_score, 10),
            })
            onCreated()
          } catch (err: any) { setError(err?.detail ?? 'Error') }
          finally { setSaving(false) }
        }} className="space-y-3 px-5 py-4">
          <div className="space-y-1">
            <label className="text-xs font-medium">Título *</label>
            <Input required placeholder="Título de la evaluación" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium">Tipo *</label>
            <select className="flex h-9 w-full rounded-md border border-input bg-background px-3 text-sm" value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              <option value="QUIZ">Quiz</option>
              <option value="PRACTICAL">Práctica</option>
            </select>
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium">Descripción</label>
            <textarea className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs font-medium">Puntaje máximo</label>
              <Input type="number" min={1} value={form.max_score} onChange={(e) => setForm({ ...form, max_score: e.target.value })} />
            </div>
            <div className="space-y-1">
              <label className="text-xs font-medium">Puntaje aprobatorio</label>
              <Input type="number" min={0} value={form.passing_score} onChange={(e) => setForm({ ...form, passing_score: e.target.value })} />
            </div>
          </div>
          {error && <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>Cancelar</Button>
            <Button type="submit" size="sm" disabled={saving}>{saving ? 'Creando…' : 'Crear evaluación'}</Button>
          </div>
        </form>
      </div>
    </div>
  )
}

function CreateQuestionModal({ evaluationId, onClose, onCreated }: {
  evaluationId: string; onClose: () => void; onCreated: () => void
}) {
  const [question, setQuestion] = useState('')
  const [options, setOptions] = useState(['', '', '', ''])
  const [correctOption, setCorrectOption] = useState(0)
  const [points, setPoints] = useState('10')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">Nueva pregunta</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted"><X size={16} /></button>
        </div>
        <form onSubmit={async (e) => {
          e.preventDefault(); setError(null); setSaving(true)
          try {
            await trainingService.createQuestion(evaluationId, {
              question: question.trim(),
              options: options.map((text, i) => ({ id: i, text: text.trim() })),
              correct_option: correctOption,
              points: parseInt(points, 10),
            })
            onCreated()
          } catch (err: any) { setError(err?.detail ?? 'Error') }
          finally { setSaving(false) }
        }} className="space-y-3 px-5 py-4">
          <div className="space-y-1">
            <label className="text-xs font-medium">Pregunta *</label>
            <textarea required className="flex min-h-[60px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring" placeholder="Texto de la pregunta" value={question} onChange={(e) => setQuestion(e.target.value)} />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium">Opciones (selecciona la correcta)</label>
            {options.map((opt, i) => (
              <div key={i} className="flex items-center gap-2">
                <input
                  type="radio"
                  name="correct"
                  checked={correctOption === i}
                  onChange={() => setCorrectOption(i)}
                  className="accent-primary"
                />
                <Input
                  required
                  placeholder={`Opción ${String.fromCharCode(65 + i)}`}
                  value={opt}
                  onChange={(e) => { const copy = [...options]; copy[i] = e.target.value; setOptions(copy) }}
                />
              </div>
            ))}
          </div>
          <div className="space-y-1">
            <label className="text-xs font-medium">Puntos</label>
            <Input type="number" min={1} value={points} onChange={(e) => setPoints(e.target.value)} className="w-24" />
          </div>
          {error && <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>Cancelar</Button>
            <Button type="submit" size="sm" disabled={saving}>{saving ? 'Creando…' : 'Crear pregunta'}</Button>
          </div>
        </form>
      </div>
    </div>
  )
}

function EnrollTeacherModal({ programId, onClose, onEnrolled }: {
  programId: string; onClose: () => void; onEnrolled: () => void
}) {
  const [email, setEmail] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-sm rounded-lg border bg-card shadow-xl">
        <div className="flex items-center justify-between border-b px-5 py-4">
          <h3 className="font-semibold">Inscribir docente</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted"><X size={16} /></button>
        </div>
        <form onSubmit={async (e) => {
          e.preventDefault(); setError(null); setSaving(true)
          try {
            // Look up user by email first
            const { api } = await import('@/lib/api')
            const users = await api.get<{ public_id: string; email: string }[]>('/auth/users')
            const user = users.find((u) => u.email === email.trim())
            if (!user) { setError('Usuario no encontrado'); setSaving(false); return }
            await trainingService.enrollTeacher(programId, user.public_id)
            onEnrolled()
          } catch (err: any) { setError(err?.detail ?? 'Error al inscribir') }
          finally { setSaving(false) }
        }} className="space-y-3 px-5 py-4">
          <div className="space-y-1">
            <label className="text-xs font-medium">Email del docente *</label>
            <Input required type="email" placeholder="docente@colegio.edu" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          {error && <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>Cancelar</Button>
            <Button type="submit" size="sm" disabled={saving}>{saving ? 'Inscribiendo…' : 'Inscribir'}</Button>
          </div>
        </form>
      </div>
    </div>
  )
}
