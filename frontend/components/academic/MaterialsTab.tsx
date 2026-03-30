'use client'

import { useState } from 'react'
import { ExternalLink, FileText, Film, Link2, Type, Trash2, Plus } from 'lucide-react'
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
  const [opening, setOpening] = useState<string | null>(null)

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

  async function handleOpen(m: MaterialRead) {
    if (m.type === 'PDF' && m.has_file) {
      setOpening(m.public_id)
      try {
        const { url } = await academicService.downloadMaterial(m.public_id)
        window.open(url, '_blank')
      } finally {
        setOpening(null)
      }
    } else if ((m.type === 'VIDEO' || m.type === 'LINK') && m.content) {
      window.open(m.content, '_blank')
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
          const canOpen = (m.type === 'PDF' && m.has_file) || ((m.type === 'VIDEO' || m.type === 'LINK') && m.content)
          return (
            <div
              key={m.public_id}
              className="rounded-md border px-3 py-2"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 min-w-0">
                  <Icon size={16} className="shrink-0 text-muted-foreground" />
                  <span className="truncate text-sm font-medium">{m.title}</span>
                  <span className="text-xs text-muted-foreground">{m.type}</span>
                  <Badge variant={m.is_published ? 'success' : 'secondary'}>
                    {m.is_published ? 'Publicado' : 'Borrador'}
                  </Badge>
                </div>
                <div className="flex items-center gap-1">
                  {canOpen && (
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={opening === m.public_id}
                      onClick={() => handleOpen(m)}
                    >
                      <ExternalLink size={14} />
                      <span className="ml-1 text-xs">
                        {opening === m.public_id ? 'Abriendo...' : 'Ver'}
                      </span>
                    </Button>
                  )}
                  {canEditContent && (
                    <>
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
                    </>
                  )}
                </div>
              </div>
              {m.type === 'TEXT' && m.content && (
                <p className="mt-2 text-sm text-muted-foreground whitespace-pre-wrap">
                  {m.content}
                </p>
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
