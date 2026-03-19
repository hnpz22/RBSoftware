'use client'

import { Button } from '@/components/ui/button'
import type { GradeWithCourses } from '@/lib/types'

interface Props {
  grades: GradeWithCourses[]
  onSelectGrade: (gradeId: string) => void
  onAssignDirector: (gradeId: string) => void
}

export function GradesTable({
  grades,
  onSelectGrade,
  onAssignDirector,
}: Props) {
  return (
    <div className="rounded-lg border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="px-4 py-3 text-left font-medium">Nombre</th>
            <th className="px-4 py-3 text-left font-medium">Director</th>
            <th className="px-4 py-3 text-left font-medium">Cursos</th>
            <th className="px-4 py-3 text-left font-medium">Activo</th>
            <th className="px-4 py-3 text-left font-medium"></th>
          </tr>
        </thead>
        <tbody>
          {grades.length === 0 && (
            <tr>
              <td
                colSpan={5}
                className="px-4 py-8 text-center text-muted-foreground"
              >
                No hay grados
              </td>
            </tr>
          )}
          {grades.map((g) => (
            <tr
              key={g.public_id}
              className="cursor-pointer border-b last:border-0 hover:bg-muted/30"
            >
              <td
                className="px-4 py-3 font-medium"
                onClick={() => onSelectGrade(g.public_id)}
              >
                {g.name}
              </td>
              <td className="px-4 py-3 text-muted-foreground">
                {g.director ? (
                  `${g.director.first_name} ${g.director.last_name}`
                ) : (
                  <span className="text-xs italic">Sin director</span>
                )}
              </td>
              <td className="px-4 py-3 text-muted-foreground">
                {g.courses?.length ?? 0}
              </td>
              <td className="px-4 py-3">
                <span
                  className={
                    g.is_active
                      ? 'text-green-600'
                      : 'text-muted-foreground'
                  }
                >
                  {g.is_active ? 'Sí' : 'No'}
                </span>
              </td>
              <td className="px-4 py-3">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={(e) => {
                    e.stopPropagation()
                    onAssignDirector(g.public_id)
                  }}
                >
                  {g.director ? 'Cambiar director' : 'Asignar director'}
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
