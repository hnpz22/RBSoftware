'use client'

import { useState } from 'react'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { CourseDetail } from '@/lib/types'
import { useAuthStore } from '@/lib/store'
import { EnrollStudentModal } from './EnrollStudentModal'

interface Props {
  course: CourseDetail
}

export function CourseStudentsTab({ course }: Props) {
  const [showEnroll, setShowEnroll] = useState(false)
  const { isAdmin, hasRole } = useAuthStore()

  const canEnroll = isAdmin() || hasRole('DIRECTOR')

  return (
    <>
      {showEnroll && (
        <EnrollStudentModal
          courseId={course.public_id}
          onClose={() => setShowEnroll(false)}
          onEnrolled={() => {
            setShowEnroll(false)
            window.location.reload()
          }}
        />
      )}

      <div className="space-y-3">
        {canEnroll && (
          <div className="flex justify-end">
            <Button size="sm" onClick={() => setShowEnroll(true)}>
              <Plus size={14} />
              <span className="ml-1">Agregar estudiante</span>
            </Button>
          </div>
        )}

        <div className="rounded-lg border">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="px-4 py-3 text-left font-medium">Nombre</th>
                <th className="px-4 py-3 text-left font-medium">Email</th>
              </tr>
            </thead>
            <tbody>
              {course.students.length === 0 && (
                <tr>
                  <td
                    colSpan={2}
                    className="px-4 py-8 text-center text-muted-foreground"
                  >
                    Sin estudiantes matriculados
                  </td>
                </tr>
              )}
              {course.students.map((s) => (
                <tr
                  key={s.public_id}
                  className="border-b last:border-0 hover:bg-muted/30"
                >
                  <td className="px-4 py-3 font-medium">
                    {s.first_name} {s.last_name}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {s.email}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
