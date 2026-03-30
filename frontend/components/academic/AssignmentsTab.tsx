'use client'

import { useState } from 'react'
import { Plus } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { AssignmentRead } from '@/lib/types'
import { CreateAssignmentModal } from './CreateAssignmentModal'
import { AssignmentDetailModal } from './AssignmentDetailModal'

interface Props {
  unitId: string
  assignments: AssignmentRead[]
  onChanged: () => void
  canEditContent?: boolean
}

export function AssignmentsTab({ unitId, assignments, onChanged, canEditContent = true }: Props) {
  const [showCreate, setShowCreate] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  return (
    <>
      {showCreate && (
        <CreateAssignmentModal
          unitId={unitId}
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false)
            onChanged()
          }}
        />
      )}
      {selectedId && (
        <AssignmentDetailModal
          assignmentId={selectedId}
          onClose={() => setSelectedId(null)}
        />
      )}

      <div className="space-y-2">
        {assignments.length === 0 && (
          <p className="py-6 text-center text-sm text-muted-foreground">
            Sin tareas
          </p>
        )}
        {assignments.map((a) => (
          <div
            key={a.public_id}
            onClick={() => setSelectedId(a.public_id)}
            className="flex cursor-pointer items-center justify-between rounded-md border px-3 py-2 hover:bg-muted/30"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{a.title}</p>
              {a.due_date && (
                <p className="text-xs text-muted-foreground">
                  Límite: {new Date(a.due_date).toLocaleDateString()}
                </p>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={a.is_published ? 'success' : 'secondary'}>
                {a.is_published ? 'Publicada' : 'Borrador'}
              </Badge>
              <span className="text-xs text-muted-foreground">
                Máx: {a.max_score}
              </span>
            </div>
          </div>
        ))}
        {canEditContent && (
          <Button
            size="sm"
            variant="outline"
            className="w-full"
            onClick={() => setShowCreate(true)}
          >
            <Plus size={14} />
            <span className="ml-2">Nueva tarea</span>
          </Button>
        )}
      </div>
    </>
  )
}
