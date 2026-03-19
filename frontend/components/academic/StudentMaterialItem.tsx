'use client'

import { useState } from 'react'
import { ExternalLink, FileText, Film, Link2, Type } from 'lucide-react'
import { Button } from '@/components/ui/button'
import * as academicService from '@/services/academic'
import type { MaterialRead } from '@/lib/types'

const TYPE_ICON: Record<string, React.ElementType> = {
  PDF: FileText,
  VIDEO: Film,
  LINK: Link2,
  TEXT: Type,
}

function isEmbeddable(url: string) {
  return /youtube\.com|youtu\.be|vimeo\.com/.test(url)
}

function toEmbedUrl(url: string): string {
  const yt = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([\w-]+)/)
  if (yt) return `https://www.youtube.com/embed/${yt[1]}`
  const vm = url.match(/vimeo\.com\/(\d+)/)
  if (vm) return `https://player.vimeo.com/video/${vm[1]}`
  return url
}

interface Props {
  material: MaterialRead
}

export function StudentMaterialItem({ material }: Props) {
  const Icon = TYPE_ICON[material.type] ?? FileText
  const [loadingUrl, setLoadingUrl] = useState(false)

  async function handleOpenPdf() {
    setLoadingUrl(true)
    try {
      const { url } = await academicService.downloadMaterial(material.public_id)
      window.open(url, '_blank')
    } finally {
      setLoadingUrl(false)
    }
  }

  return (
    <div className="rounded-md border p-3">
      <div className="flex items-center gap-2 mb-1">
        <Icon size={14} className="text-muted-foreground" />
        <span className="text-sm font-medium">{material.title}</span>
      </div>

      {material.type === 'TEXT' && material.content && (
        <p className="mt-1 text-sm text-muted-foreground whitespace-pre-wrap">
          {material.content}
        </p>
      )}

      {material.type === 'PDF' && (
        <Button
          size="sm"
          variant="outline"
          className="mt-1"
          disabled={loadingUrl}
          onClick={handleOpenPdf}
        >
          <ExternalLink size={12} />
          <span className="ml-1">{loadingUrl ? 'Cargando…' : 'Ver PDF'}</span>
        </Button>
      )}

      {material.type === 'VIDEO' &&
        material.content &&
        (isEmbeddable(material.content) ? (
          <div className="mt-2 aspect-video overflow-hidden rounded-md">
            <iframe
              src={toEmbedUrl(material.content)}
              className="h-full w-full"
              allowFullScreen
            />
          </div>
        ) : (
          <Button
            size="sm"
            variant="outline"
            className="mt-1"
            onClick={() => window.open(material.content!, '_blank')}
          >
            <ExternalLink size={12} />
            <span className="ml-1">Ver video</span>
          </Button>
        ))}

      {material.type === 'LINK' && material.content && (
        <Button
          size="sm"
          variant="outline"
          className="mt-1"
          onClick={() => window.open(material.content!, '_blank')}
        >
          <ExternalLink size={12} />
          <span className="ml-1">Abrir enlace</span>
        </Button>
      )}
    </div>
  )
}
