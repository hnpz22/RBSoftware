'use client'

import { useState } from 'react'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import type { CourseDetail } from '@/lib/types'
import { EnrollStudentModal } from './EnrollStudentModal'

interface Props {
  course: CourseDetail
}

export function CourseStudentsTab({ course }: Props) {
  const [showEnroll, setShowEnroll] = useState(false)

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

      <div className="space-y-2">
        {course.students.length === 0 && (
          <p className="py-6 text-center text-sm text-muted-foreground">
            Sin estudiantes
          </p>
        )}
        {course.students.map((s) => (
          <div
            key={s.public_id}
            className="flex items-center justify-between rounded-md border px-3 py-2"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">
                {s.first_name} {s.last_name}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                {s.email}
              </p>
            </div>
          </div>
        ))}
        <Button
          size="sm"
          variant="outline"
          className="w-full"
          onClick={() => setShowEnroll(true)}
        >
          <Plus size={14} />
          <span className="ml-2">Agregar estudiante</span>
        </Button>
      </div>
    </>
  )
}
