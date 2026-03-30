'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import type { CourseDetail, UnitRead } from '@/lib/types'
import { useUnitContent } from '@/hooks/useUnitContent'
import * as academicService from '@/services/academic'
import { MaterialsTab } from './MaterialsTab'
import { AssignmentsTab } from './AssignmentsTab'

interface Props {
  unit: UnitRead | null
  course: CourseDetail
  onUnitChanged: () => void
}

type Tab = 'materials' | 'assignments'

export function UnitDetailPanel({ unit, course, onUnitChanged }: Props) {
  const [tab, setTab] = useState<Tab>('materials')
  const { materials, assignments, loading, reload } = useUnitContent(
    unit?.public_id ?? null,
  )
  const [toggling, setToggling] = useState(false)

  if (!unit) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted-foreground">
        Selecciona una unidad
      </div>
    )
  }

  async function handleTogglePublish() {
    if (!unit) return
    setToggling(true)
    try {
      if (unit.is_published) {
        await academicService.unpublishUnit(unit.public_id)
      } else {
        await academicService.publishUnit(unit.public_id)
      }
      onUnitChanged()
    } finally {
      setToggling(false)
    }
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: 'materials', label: 'Materiales' },
    { key: 'assignments', label: 'Tareas' },
  ]

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="shrink-0 border-b px-4 py-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">{unit.title}</h2>
          <Button
            size="sm"
            variant="outline"
            disabled={toggling}
            onClick={handleTogglePublish}
          >
            {unit.is_published ? 'Despublicar' : 'Publicar'}
          </Button>
        </div>
        {unit.description && (
          <p className="mt-1 text-sm text-muted-foreground">
            {unit.description}
          </p>
        )}
      </div>

      <div className="flex shrink-0 border-b">
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

      <div className="flex-1 overflow-y-auto p-4">
        {loading && (
          <p className="py-8 text-center text-muted-foreground">Cargando…</p>
        )}
        {!loading && tab === 'materials' && (
          <MaterialsTab
            unitId={unit.public_id}
            materials={materials}
            onChanged={reload}
          />
        )}
        {!loading && tab === 'assignments' && (
          <AssignmentsTab
            unitId={unit.public_id}
            assignments={assignments}
            onChanged={reload}
          />
        )}
      </div>
    </div>
  )
}
