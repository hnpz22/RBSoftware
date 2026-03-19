'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useGradeDetail } from '@/hooks/useGradeDetail'
import type { GradeStudent } from '@/hooks/useGradeDetail'
import { TransferStudentModal } from './TransferStudentModal'

interface Props {
  gradeId: string
}

type Tab = 'courses' | 'students'

export function GradeDetailView({ gradeId }: Props) {
  const router = useRouter()
  const { grade, courseRows, students, loading, reload } =
    useGradeDetail(gradeId)
  const [tab, setTab] = useState<Tab>('courses')
  const [transferring, setTransferring] = useState<GradeStudent | null>(null)

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        Cargando…
      </div>
    )
  }

  if (!grade) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        Grado no encontrado
      </div>
    )
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: 'courses', label: 'Cursos' },
    { key: 'students', label: 'Estudiantes del grado' },
  ]

  return (
    <>
      {transferring && (
        <TransferStudentModal
          student={transferring}
          courses={courseRows}
          onClose={() => setTransferring(null)}
          onTransferred={() => {
            setTransferring(null)
            reload()
          }}
        />
      )}

      <div className="space-y-4">
        {/* Header */}
        <div>
          <button
            onClick={() => router.push('/academic/grades')}
            className="mb-2 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft size={14} /> Mis Grados
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold">{grade.name}</h1>
              {grade.director && (
                <p className="text-sm text-muted-foreground">
                  Director: {grade.director.first_name}{' '}
                  {grade.director.last_name}
                </p>
              )}
            </div>
            <Button variant="outline" size="sm" onClick={reload}>
              <RefreshCw size={14} />
              <span className="ml-2">Actualizar</span>
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2 text-sm font-medium border-b-2 ${
                tab === t.key
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Courses tab */}
        {tab === 'courses' && (
          <div className="rounded-lg border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium">Nombre</th>
                  <th className="px-4 py-3 text-left font-medium">Docente</th>
                  <th className="px-4 py-3 text-left font-medium">
                    Estudiantes
                  </th>
                  <th className="px-4 py-3 text-left font-medium">Activo</th>
                </tr>
              </thead>
              <tbody>
                {courseRows.length === 0 && (
                  <tr>
                    <td
                      colSpan={4}
                      className="px-4 py-8 text-center text-muted-foreground"
                    >
                      Sin cursos
                    </td>
                  </tr>
                )}
                {courseRows.map((c) => (
                  <tr
                    key={c.public_id}
                    onClick={() =>
                      router.push(`/academic/courses/${c.public_id}`)
                    }
                    className="cursor-pointer border-b last:border-0 hover:bg-muted/30"
                  >
                    <td className="px-4 py-3 font-medium">{c.name}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {c.teacher
                        ? `${c.teacher.first_name} ${c.teacher.last_name}`
                        : '—'}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {c.studentCount}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={
                          c.is_active
                            ? 'text-green-600'
                            : 'text-muted-foreground'
                        }
                      >
                        {c.is_active ? 'Sí' : 'No'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Students tab */}
        {tab === 'students' && (
          <div className="rounded-lg border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="px-4 py-3 text-left font-medium">Nombre</th>
                  <th className="px-4 py-3 text-left font-medium">Email</th>
                  <th className="px-4 py-3 text-left font-medium">
                    Curso actual
                  </th>
                  <th className="px-4 py-3 text-left font-medium"></th>
                </tr>
              </thead>
              <tbody>
                {students.length === 0 && (
                  <tr>
                    <td
                      colSpan={4}
                      className="px-4 py-8 text-center text-muted-foreground"
                    >
                      Sin estudiantes
                    </td>
                  </tr>
                )}
                {students.map((s) => (
                  <tr
                    key={`${s.user.public_id}-${s.courseId}`}
                    className="border-b last:border-0"
                  >
                    <td className="px-4 py-3 font-medium">
                      {s.user.first_name} {s.user.last_name}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {s.user.email}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {s.courseName}
                    </td>
                    <td className="px-4 py-3">
                      {courseRows.length > 1 && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setTransferring(s)}
                        >
                          Transferir
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  )
}
