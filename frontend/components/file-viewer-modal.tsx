'use client'

import { useEffect, useState } from 'react'
import { Download, ExternalLink, Loader2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import * as academicService from '@/services/academic'
import { useAuthStore } from '@/lib/store'

interface Props {
  isOpen: boolean
  onClose: () => void
  materialId: string | null
  fileName: string
  fileType: 'PDF' | 'IMAGE'
}

export function FileViewerModal({ isOpen, onClose, materialId, fileName, fileType }: Props) {
  const [url, setUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const isAdmin = useAuthStore((s) => s.isAdmin)

  useEffect(() => {
    if (!isOpen || !materialId) {
      setUrl(null)
      setError(null)
      return
    }
    setLoading(true)
    setError(null)
    academicService
      .viewMaterial(materialId)
      .then((res) => setUrl(res.url))
      .catch((err: any) => setError(err?.detail ?? 'Error al obtener el archivo'))
      .finally(() => setLoading(false))
  }, [isOpen, materialId])

  const handleDownload = () => {
    if (!materialId) return
    academicService
      .downloadMaterial(materialId)
      .then((res) => window.open(res.url, '_blank'))
      .catch((err: any) => setError(err?.detail ?? 'Error al descargar el archivo'))
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="flex h-full w-full flex-col bg-background md:h-[90vh] md:max-h-[90vh] md:w-[90vw] md:max-w-[90vw] md:rounded-lg md:border md:shadow-xl">
        <div className="flex shrink-0 items-center justify-between border-b px-4 py-3">
          <h3 className="truncate text-sm font-semibold">{fileName}</h3>
          <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
            <X size={16} />
          </button>
        </div>

        <div className="flex flex-1 items-center justify-center overflow-hidden p-2">
          {loading && (
            <div className="flex flex-col items-center gap-2 text-muted-foreground">
              <Loader2 size={24} className="animate-spin" />
              <span className="text-sm">Cargando archivo…</span>
            </div>
          )}

          {error && (
            <div className="flex flex-col items-center gap-3 text-center">
              <p className="text-sm text-destructive">{error}</p>
              {url && (
                <Button size="sm" variant="outline" onClick={() => window.open(url, '_blank')}>
                  <ExternalLink size={14} />
                  <span className="ml-1">Abrir en nueva pestaña</span>
                </Button>
              )}
            </div>
          )}

          {!loading && !error && url && fileType === 'PDF' && (
            <iframe
              src={`${url}#toolbar=0&navpanes=0&scrollbar=1`}
              className="h-full w-full border-0"
              title={fileName}
            />
          )}

          {!loading && !error && url && fileType === 'IMAGE' && (
            <img
              src={url}
              alt={fileName}
              className="max-h-full max-w-full object-contain mx-auto"
              onContextMenu={(e) => e.preventDefault()}
              draggable={false}
            />
          )}
        </div>

        <div className="flex shrink-0 items-center justify-between border-t px-4 py-3">
          <div className="md:hidden">
            {!loading && url && fileType === 'PDF' && (
              <Button size="sm" variant="outline" onClick={() => window.open(url, '_blank')}>
                <ExternalLink size={14} />
                <span className="ml-1">Abrir en nueva pestaña</span>
              </Button>
            )}
          </div>
          <div className="flex items-center gap-2 ml-auto">
            {!loading && url && isAdmin() && (
              <Button size="sm" variant="outline" onClick={handleDownload}>
                <Download size={14} />
                <span className="ml-1">Descargar</span>
              </Button>
            )}
            <Button size="sm" variant="outline" onClick={onClose}>
              Cerrar
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
