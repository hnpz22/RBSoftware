'use client'

import { useState } from 'react'
import { FileText, Film, Link2, Type, Trash2, Plus } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import * as academicService from '@/services/academic'
import type { MaterialRead } from '@/lib/types'
import { AddMaterialModal } from './AddMaterialModal'

const TYPE_ICON: Record<string, React.ElementType> = {
  PDF: FileText,
  VIDEO: Film,
  LINK: Link2,
  TEXT: Type,
}

interface Props {
  unitId: string
  materials: MaterialRead[]
  onChanged: () => void
  canEditContent?: boolean
}

export function MaterialsTab({ unitId, materials, onChanged, canEditContent = true }: Props) {
  const [showAdd, setShowAdd] = useState(false)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [toggling, setToggling] = useState<string | null>(null)

  async function handleDelete(id: string) {
    setDeleting(id)
    try {
      await academicService.deleteMaterial(id)
      onChanged()
    } finally {
      setDeleting(null)
    }
  }

  async function handleTogglePublish(id: string, isPublished: boolean) {
    setToggling(id)
    try {
      if (isPublished) {
        await academicService.unpublishMaterial(id)
      } else {
        await academicService.publishMaterial(id)
      }
      onChanged()
    } finally {
      setToggling(null)
    }
  }

  return (
    <>
      {showAdd && (
        <AddMaterialModal
          unitId={unitId}
          onClose={() => setShowAdd(false)}
          onCreated={() => {
            setShowAdd(false)
            onChanged()
          }}
        />
      )}

      <div className="space-y-2">
        {materials.length === 0 && (
          <p className="py-6 text-center text-sm text-muted-foreground">
            Sin materiales
          </p>
        )}
        {materials.map((m) => {
          const Icon = TYPE_ICON[m.type] ?? FileText
          return (
            <div
              key={m.public_id}
              className="flex items-center justify-between rounded-md border px-3 py-2"
            >
              <div className="flex items-center gap-2 min-w-0">
                <Icon size={16} className="shrink-0 text-muted-foreground" />
                <span className="truncate text-sm">{m.title}</span>
                <span className="text-xs text-muted-foreground">{m.type}</span>
                <Badge variant={m.is_published ? 'success' : 'secondary'}>
                  {m.is_published ? 'Publicado' : 'Borrador'}
                </Badge>
              </div>
              {canEditContent && (
                <div className="flex items-center gap-1">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={toggling === m.public_id}
                    onClick={() => handleTogglePublish(m.public_id, m.is_published)}
                  >
                    {m.is_published ? 'Despublicar' : 'Publicar'}
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    disabled={deleting === m.public_id}
                    onClick={() => handleDelete(m.public_id)}
                  >
                    <Trash2 size={14} className="text-destructive" />
                  </Button>
                </div>
              )}
            </div>
          )
        })}
        {canEditContent && (
          <Button
            size="sm"
            variant="outline"
            className="w-full"
            onClick={() => setShowAdd(true)}
          >
            <Plus size={14} />
            <span className="ml-2">Agregar material</span>
          </Button>
        )}
      </div>
    </>
  )
}
