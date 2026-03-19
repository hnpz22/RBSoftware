'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import type { StudentUnitContent } from '@/lib/types'
import { StudentMaterialItem } from './StudentMaterialItem'
import { StudentAssignmentItem } from './StudentAssignmentItem'

interface Props {
  unit: StudentUnitContent
  onSubmitted: () => void
}

export function StudentUnitSection({ unit, onSubmitted }: Props) {
  const [open, setOpen] = useState(true)

  return (
    <div className="rounded-lg border">
      <button
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-2 px-4 py-3 text-left hover:bg-muted/30"
      >
        {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
        <h3 className="font-semibold">{unit.title}</h3>
      </button>

      {open && (
        <div className="border-t px-4 py-3 space-y-4">
          {/* Materials */}
          {unit.materials.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Materiales
              </p>
              {unit.materials.map((m) => (
                <StudentMaterialItem key={m.public_id} material={m} />
              ))}
            </div>
          )}

          {/* Assignments */}
          {unit.assignments.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Tareas
              </p>
              {unit.assignments.map((a) => (
                <StudentAssignmentItem
                  key={a.public_id}
                  assignment={a}
                  onSubmitted={onSubmitted}
                />
              ))}
            </div>
          )}

          {unit.materials.length === 0 && unit.assignments.length === 0 && (
            <p className="text-sm text-muted-foreground">Sin contenido</p>
          )}
        </div>
      )}
    </div>
  )
}
