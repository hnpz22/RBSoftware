'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Award,
  BookOpen,
  CheckCircle2,
  ClipboardCheck,
  RefreshCw,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import * as trainingService from '@/services/training'
import type { TeacherProgramProgress } from '@/lib/types'

export function MyProgramsView() {
  const router = useRouter()
  const [programs, setPrograms] = useState<TeacherProgramProgress[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      setPrograms(await trainingService.getMyPrograms())
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar programas')
      setPrograms([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Mis Programas</h1>
          <p className="text-sm text-muted-foreground">
            {programs.length} programa{programs.length !== 1 && 's'} inscrito
            {programs.length !== 1 && 's'}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span className="ml-2">Actualizar</span>
        </Button>
      </div>

      {loading && (
        <p className="py-12 text-center text-muted-foreground">Cargando…</p>
      )}

      {!loading && error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-sm text-destructive">
          {error}
        </div>
      )}

      {!loading && !error && programs.length === 0 && (
        <p className="py-12 text-center text-muted-foreground">
          No estás inscrito en ningún programa
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {programs.map((p) => {
          const lessonPct =
            p.total_lessons > 0
              ? Math.round((p.completed_lessons / p.total_lessons) * 100)
              : 0

          return (
            <div
              key={p.program_id}
              className="rounded-lg border bg-card p-5 transition-colors hover:bg-muted/30"
            >
              <div className="flex items-start justify-between">
                <h3 className="font-medium">{p.program_name}</h3>
                {p.is_certified && (
                  <span className="flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
                    <Award size={12} />
                    Certificado
                  </span>
                )}
              </div>

              {/* Progress bar */}
              <div className="mt-4">
                <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <BookOpen size={12} />
                    Lecciones
                  </span>
                  <span>
                    {p.completed_lessons}/{p.total_lessons}
                  </span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-blue-600 transition-all"
                    style={{ width: `${lessonPct}%` }}
                  />
                </div>
              </div>

              {/* Evaluations */}
              <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <ClipboardCheck size={12} />
                  Evaluaciones aprobadas
                </span>
                <span>
                  {p.passed_evaluations}/{p.total_evaluations}
                </span>
              </div>

              {/* Score */}
              {p.overall_score !== null && (
                <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <CheckCircle2 size={12} />
                    Puntaje promedio
                  </span>
                  <span className="font-medium">{p.overall_score}</span>
                </div>
              )}

              {/* Certificate code */}
              {p.certificate_code && (
                <div className="mt-3 rounded-md bg-green-50 px-3 py-1.5 text-xs text-green-700 dark:bg-green-900/20 dark:text-green-400">
                  Código: {p.certificate_code}
                </div>
              )}

              <Button
                variant="outline"
                size="sm"
                className="mt-4 w-full"
                onClick={() =>
                  router.push(`/training/programs/${p.program_id}`)
                }
              >
                {p.is_certified ? 'Ver programa' : 'Continuar'}
              </Button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
