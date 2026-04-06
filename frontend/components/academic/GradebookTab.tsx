'use client'

import { useEffect, useState } from 'react'
import { Download, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import * as academicService from '@/services/academic'
import type { Gradebook } from '@/lib/types'

interface Props {
  courseId: string
  courseName: string
}

function exportToCSV(gradebook: Gradebook) {
  const headers = [
    'Estudiante',
    ...gradebook.assignments.map((a) => a.title),
    'Promedio',
  ]
  const rows = gradebook.students.map((s) => [
    `${s.student.first_name} ${s.student.last_name}`,
    ...gradebook.assignments.map((a) => {
      const g = s.grades[a.public_id]
      return g?.score ?? '-'
    }),
    s.average ?? '-',
  ])
  const csv = [headers, ...rows].map((r) => r.join(',')).join('\n')
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `planilla-${gradebook.course.name}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

function scoreColor(score: number | null | undefined, max: number) {
  if (score == null) return 'text-muted-foreground'
  const pct = (score / max) * 100
  return pct >= 60
    ? 'text-green-700 dark:text-green-400'
    : 'text-red-700 dark:text-red-400'
}

function avgColor(avg: number | null) {
  if (avg == null) return 'text-muted-foreground'
  return avg >= 60
    ? 'text-green-700 dark:text-green-400 font-semibold'
    : 'text-red-700 dark:text-red-400 font-semibold'
}

function round(n: number, d: number) {
  const f = 10 ** d
  return Math.round(n * f) / f
}

export function GradebookTab({ courseId }: Props) {
  const [gradebook, setGradebook] = useState<Gradebook | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    academicService
      .getGradebook(courseId)
      .then(setGradebook)
      .catch((err: any) => setError(err?.detail ?? 'Error al cargar planilla'))
      .finally(() => setLoading(false))
  }, [courseId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        <Loader2 size={24} className="animate-spin mr-2" />
        Cargando planilla…
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-sm text-destructive m-4">
        {error}
      </div>
    )
  }

  if (!gradebook) return null

  const { assignments, students } = gradebook

  const classAverages = assignments.map((a) => {
    const scores = students
      .map((s) => s.grades[a.public_id]?.score)
      .filter((s): s is number => s != null)
    return scores.length ? round(scores.reduce((acc, s) => acc + s, 0) / scores.length, 1) : null
  })

  const globalAvg = (() => {
    const avgs = students.map((s) => s.average).filter((a): a is number => a != null)
    return avgs.length ? round(avgs.reduce((acc, a) => acc + a, 0) / avgs.length, 1) : null
  })()

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center justify-between px-4 py-3 border-b">
        <h2 className="text-sm font-semibold">Planilla de calificaciones</h2>
        <Button variant="outline" size="sm" onClick={() => exportToCSV(gradebook)}>
          <Download size={14} />
          <span className="ml-1">Exportar CSV</span>
        </Button>
      </div>

      <div className="flex-1 overflow-auto">
        {assignments.length === 0 ? (
          <p className="py-20 text-center text-sm text-muted-foreground">
            No hay tareas creadas en este curso
          </p>
        ) : (
          <table className="w-full text-sm border-collapse">
            <thead className="sticky top-0 z-10 bg-background">
              <tr className="border-b">
                <th className="sticky left-0 z-20 bg-background text-left px-4 py-2 font-medium min-w-[180px]">
                  Estudiante
                </th>
                {assignments.map((a) => (
                  <th key={a.public_id} className="px-3 py-2 text-center font-medium min-w-[100px]">
                    <div className="truncate max-w-[120px] mx-auto" title={a.title}>
                      {a.title.length > 15 ? a.title.slice(0, 15) + '…' : a.title}
                    </div>
                    <div className="text-xs text-muted-foreground font-normal">/{a.max_score}</div>
                  </th>
                ))}
                <th className="px-3 py-2 text-center font-medium min-w-[90px]">Promedio</th>
              </tr>
            </thead>
            <tbody>
              {students.length === 0 ? (
                <tr>
                  <td colSpan={assignments.length + 2} className="py-8 text-center text-muted-foreground">
                    No hay estudiantes matriculados
                  </td>
                </tr>
              ) : (
                <>
                  {students.map((s) => (
                    <tr key={s.student.public_id} className="border-b hover:bg-muted/30">
                      <td className="sticky left-0 z-10 bg-background px-4 py-2">
                        <div className="font-medium">
                          {s.student.first_name} {s.student.last_name}
                        </div>
                        <div className="text-xs text-muted-foreground">{s.student.email}</div>
                      </td>
                      {assignments.map((a) => {
                        const g = s.grades[a.public_id]
                        return (
                          <td key={a.public_id} className="px-3 py-2 text-center">
                            {g == null ? (
                              <span className="text-muted-foreground">—</span>
                            ) : g.status === 'GRADED' && g.score != null ? (
                              <span className={scoreColor(g.score, a.max_score)}>
                                {g.score}/{a.max_score}
                              </span>
                            ) : g.status === 'SUBMITTED' ? (
                              <Badge variant="warning" className="text-xs">
                                Por calificar
                              </Badge>
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </td>
                        )
                      })}
                      <td className={`px-3 py-2 text-center ${avgColor(s.average)}`}>
                        {s.average != null ? s.average : '—'}
                      </td>
                    </tr>
                  ))}
                  <tr className="border-t-2 bg-muted/20 font-medium">
                    <td className="sticky left-0 z-10 bg-muted/20 px-4 py-2">Promedio clase</td>
                    {classAverages.map((avg, i) => (
                      <td
                        key={assignments[i].public_id}
                        className={`px-3 py-2 text-center ${avgColor(avg)}`}
                      >
                        {avg != null ? avg : '—'}
                      </td>
                    ))}
                    <td className={`px-3 py-2 text-center ${avgColor(globalAvg)}`}>
                      {globalAvg != null ? globalAvg : '—'}
                    </td>
                  </tr>
                </>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
