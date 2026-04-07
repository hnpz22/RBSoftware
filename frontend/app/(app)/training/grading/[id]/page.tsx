'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, Award, CheckCircle2, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'

interface GradebookEval {
  public_id: string
  title: string
  type: string
  max_score: number
  passing_score: number
}

interface GradebookGrade {
  score: number
  status: string
  submission_id: string
  type: string
}

interface GradebookTeacher {
  teacher: { public_id: string; first_name: string; last_name: string; email: string }
  grades: Record<string, GradebookGrade | null>
  average: number | null
  completed: number
  total: number
  is_certified: boolean
}

interface Gradebook {
  program: { public_id: string; name: string }
  evaluations: GradebookEval[]
  teachers: GradebookTeacher[]
}

export default function GradebookDetailPage() {
  const params = useParams()
  const router = useRouter()
  const programId = params.id as string

  const [data, setData] = useState<Gradebook | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      setData(await api.get<Gradebook>(`/training/programs/${programId}/gradebook`))
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar planilla')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [programId])

  if (loading) return <p className="py-12 text-center text-muted-foreground">Cargando…</p>
  if (error) return <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-sm text-destructive">{error}</div>
  if (!data) return null

  return (
    <div className="space-y-4">
      <div>
        <button
          onClick={() => router.push('/training/grading')}
          className="mb-2 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft size={14} /> Calificaciones
        </button>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">{data.program.name}</h1>
          <Button variant="outline" size="sm" onClick={load}>
            <RefreshCw size={14} className="mr-1" /> Actualizar
          </Button>
        </div>
        <p className="text-sm text-muted-foreground">
          {data.teachers.length} docente{data.teachers.length !== 1 && 's'} · {data.evaluations.length} evaluacion{data.evaluations.length !== 1 && 'es'}
        </p>
      </div>

      {data.teachers.length === 0 ? (
        <p className="py-12 text-center text-muted-foreground">No hay docentes inscritos</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="sticky left-0 bg-muted/50 px-4 py-3 text-left font-medium">Docente</th>
                {data.evaluations.map((ev) => (
                  <th key={ev.public_id} className="px-4 py-3 text-center font-medium min-w-[120px]">
                    <div>{ev.title}</div>
                    <div className="text-[10px] font-normal text-muted-foreground">
                      {ev.type === 'QUIZ' ? 'Quiz' : 'Práctica'} · {ev.passing_score}/{ev.max_score}
                    </div>
                  </th>
                ))}
                <th className="px-4 py-3 text-center font-medium">Promedio</th>
                <th className="px-4 py-3 text-center font-medium">Cert.</th>
              </tr>
            </thead>
            <tbody>
              {data.teachers.map((t) => (
                <tr key={t.teacher.public_id} className="border-b hover:bg-muted/30">
                  <td className="sticky left-0 bg-card px-4 py-3">
                    <p className="font-medium">{t.teacher.first_name} {t.teacher.last_name}</p>
                    <p className="text-xs text-muted-foreground">{t.teacher.email}</p>
                  </td>
                  {data.evaluations.map((ev) => {
                    const grade = t.grades[ev.public_id]
                    if (!grade) {
                      return <td key={ev.public_id} className="px-4 py-3 text-center text-muted-foreground">—</td>
                    }
                    const passed = grade.score >= ev.passing_score
                    return (
                      <td key={ev.public_id} className="px-4 py-3 text-center">
                        <span className={`font-medium ${passed ? 'text-green-600' : 'text-red-600'}`}>
                          {grade.score}/{ev.max_score}
                        </span>
                      </td>
                    )
                  })}
                  <td className="px-4 py-3 text-center">
                    {t.average !== null ? (
                      <span className="font-semibold">{t.average}</span>
                    ) : (
                      <span className="text-muted-foreground">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {t.is_certified ? (
                      <Award size={18} className="mx-auto text-green-600" />
                    ) : (
                      <span className="text-xs text-muted-foreground">{t.completed}/{t.total}</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
