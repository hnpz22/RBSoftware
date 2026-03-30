'use client'

import { Plus } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { UnitRead } from '@/lib/types'

interface Props {
  units: UnitRead[]
  selectedId: string | null
  onSelect: (id: string) => void
  onCreateUnit: () => void
  canEditContent?: boolean
}

export function UnitsSidebar({ units, selectedId, onSelect, onCreateUnit, canEditContent = true }: Props) {
  return (
    <div className="flex w-64 shrink-0 flex-col border-r bg-muted/20">
      <div className="flex items-center justify-between border-b px-3 py-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Unidades
        </p>
        {canEditContent && (
          <Button size="sm" variant="ghost" onClick={onCreateUnit}>
            <Plus size={14} />
          </Button>
        )}
      </div>
      <div className="flex-1 overflow-y-auto">
        {units.length === 0 && (
          <p className="px-3 py-6 text-center text-xs text-muted-foreground">
            Sin unidades
          </p>
        )}
        {units.map((u) => (
          <button
            key={u.public_id}
            onClick={() => onSelect(u.public_id)}
            className={`w-full border-b px-3 py-3 text-left transition-colors ${
              selectedId === u.public_id
                ? 'bg-primary/10 border-l-2 border-l-primary'
                : 'hover:bg-muted/40'
            }`}
          >
            <p className="truncate text-sm font-medium">{u.title}</p>
            <Badge
              variant={u.is_published ? 'success' : 'secondary'}
              className="mt-1"
            >
              {u.is_published ? 'Publicada' : 'Borrador'}
            </Badge>
          </button>
        ))}
      </div>
    </div>
  )
}
