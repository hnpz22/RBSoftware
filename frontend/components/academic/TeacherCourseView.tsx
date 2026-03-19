'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import type { CourseDetail, UnitRead } from '@/lib/types'
import { UnitsSidebar } from './UnitsSidebar'
import { UnitDetailPanel } from './UnitDetailPanel'
import { CreateUnitModal } from './CreateUnitModal'

interface Props {
  course: CourseDetail
  units: UnitRead[]
  reload: () => void
}

export function TeacherCourseView({ course, units, reload }: Props) {
  const router = useRouter()
  const [selectedUnitId, setSelectedUnitId] = useState<string | null>(
    units[0]?.public_id ?? null,
  )
  const [showCreateUnit, setShowCreateUnit] = useState(false)

  const selectedUnit = units.find((u) => u.public_id === selectedUnitId) ?? null

  return (
    <>
      {showCreateUnit && (
        <CreateUnitModal
          courseId={course.public_id}
          onClose={() => setShowCreateUnit(false)}
          onCreated={() => {
            setShowCreateUnit(false)
            reload()
          }}
        />
      )}

      <div className="flex h-full flex-col">
        <div className="shrink-0 border-b px-4 py-3">
          <button
            onClick={() => router.push('/academic/courses')}
            className="mb-1 flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft size={12} /> Mis Cursos
          </button>
          <h1 className="text-lg font-semibold">{course.name}</h1>
          <p className="text-xs text-muted-foreground">
            Docente: {course.teacher.first_name} {course.teacher.last_name}
            {' · '}
            {course.students.length} estudiantes
          </p>
        </div>

        <div className="flex flex-1 overflow-hidden">
          <UnitsSidebar
            units={units}
            selectedId={selectedUnitId}
            onSelect={setSelectedUnitId}
            onCreateUnit={() => setShowCreateUnit(true)}
          />
          <UnitDetailPanel
            unit={selectedUnit}
            course={course}
            onUnitChanged={reload}
          />
        </div>
      </div>
    </>
  )
}
