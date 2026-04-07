'use client'

import { useEffect, useState, useCallback } from 'react'
import { AlertCircle, Download, FileText, Image as ImageIcon, Loader2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import * as academicService from '@/services/academic'
import { useAuthStore } from '@/lib/store'
import { PDFHighlighterViewer } from './pdf-highlighter'

interface Props {
  isOpen: boolean
  onClose: () => void
  fileName: string
  fileType?: 'PDF' | 'IMAGE' | 'auto'
  materialId?: string | null
  submissionId?: string | null
  localUrl?: string | null
}

function detectType(fileName: string, contentType?: string): 'PDF' | 'IMAGE' {
  const ext = fileName?.split('.').pop()?.toLowerCase()
  if (contentType?.includes('pdf') || ext === 'pdf') return 'PDF'
  if (contentType?.startsWith('image/') || ['png', 'jpg', 'jpeg', 'gif', 'webp'].includes(ext ?? ''))
    return 'IMAGE'
  return 'PDF'
}

export function FileViewerModal({
  isOpen,
  onClose,
  fileName,
  fileType = 'auto',
  materialId,
  submissionId,
  localUrl,
}: Props) {
  const [url, setUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [resolvedType, setResolvedType] = useState<'PDF' | 'IMAGE' | null>(null)
  const [visible, setVisible] = useState(false)
  const isAdmin = useAuthStore((s) => s.isAdmin)

  useEffect(() => {
    if (isOpen) {
      requestAnimationFrame(() => setVisible(true))
    } else {
      setVisible(false)
      setUrl(null)
      setError(null)
      setResolvedType(null)
    }
  }, [isOpen])

  useEffect(() => {
    if (!isOpen) return

    if (localUrl) {
      setUrl(localUrl)
      setResolvedType(fileType !== 'auto' ? fileType : detectType(fileName))
      setLoading(false)
      return
    }

    const fetchUrl = submissionId
      ? academicService.viewSubmission(submissionId).then((res) => {
          setResolvedType(
            fileType !== 'auto'
              ? fileType
              : detectType(res.file_name ?? fileName, (res as any).content_type),
          )
          return res.url
        })
      : materialId
        ? academicService.viewMaterial(materialId).then((res) => {
            setResolvedType(fileType !== 'auto' ? fileType : detectType(fileName))
            return res.url
          })
        : null

    if (!fetchUrl) return

    setLoading(true)
    setError(null)
    fetchUrl
      .then((u) => setUrl(u))
      .catch((err: any) => setError(err?.detail ?? 'Error al obtener el archivo'))
      .finally(() => setLoading(false))
  }, [isOpen, localUrl, submissionId, materialId, fileName, fileType])

  const handleClose = useCallback(() => {
    setVisible(false)
    setTimeout(onClose, 200)
  }, [onClose])

  useEffect(() => {
    if (!isOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') handleClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [isOpen, handleClose])

  if (!isOpen) return null

  const TypeIcon = resolvedType === 'IMAGE' ? ImageIcon : FileText

  return (
    <div
      className={`fixed inset-0 z-[200] flex items-center justify-center bg-black/60 transition-opacity duration-200 ${visible ? 'opacity-100' : 'opacity-0'}`}
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose()
      }}
    >
      <div
        className={`flex flex-col bg-background transition-all duration-200 ${visible ? 'scale-100 opacity-100' : 'scale-95 opacity-0'} h-full w-full md:h-[90vh] md:max-h-[90vh] md:max-w-4xl md:rounded-lg md:border md:shadow-xl`}
      >
        {/* Header */}
        <div className="flex shrink-0 items-center gap-2 border-b px-4 py-3">
          <TypeIcon size={16} className="shrink-0 text-muted-foreground" />
          <h3 className="min-w-0 flex-1 truncate text-sm font-semibold">{fileName}</h3>
          <button onClick={handleClose} className="rounded-md p-1 hover:bg-muted">
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {loading && (
            <div className="flex flex-1 flex-col items-center justify-center gap-2 text-muted-foreground">
              <Loader2 size={24} className="animate-spin" />
              <span className="text-sm">Cargando archivo…</span>
            </div>
          )}

          {error && (
            <div className="flex flex-1 flex-col items-center justify-center gap-3">
              <AlertCircle className="text-destructive" size={32} />
              <p className="text-sm text-muted-foreground">No se pudo cargar el archivo</p>
              {url && (
                <Button variant="outline" size="sm" onClick={() => window.open(url, '_blank')}>
                  Abrir en nueva pestaña
                </Button>
              )}
            </div>
          )}

          {!loading && !error && url && resolvedType === 'PDF' && materialId && (
            <div className="flex flex-1 flex-col overflow-hidden">
              <PDFHighlighterViewer url={url} materialId={materialId} fileName={fileName} />
            </div>
          )}

          {!loading && !error && url && resolvedType === 'PDF' && !materialId && (
            <div className="flex flex-1 flex-col overflow-hidden">
              <iframe
                src={`${url}#toolbar=0&navpanes=0`}
                className="w-full h-full border-0"
                title={fileName}
              />
            </div>
          )}

          {!loading && !error && url && resolvedType === 'IMAGE' && (
            <div className="flex flex-1 items-center justify-center bg-muted/20 p-4">
              <img
                src={url}
                alt={fileName}
                className="max-h-full max-w-full rounded object-contain"
                onContextMenu={(e) => e.preventDefault()}
                draggable={false}
              />
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex shrink-0 items-center justify-between border-t px-4 py-3">
          <div className="flex items-center gap-2">
            {materialId && resolvedType === 'PDF' && (
              <span className="text-xs text-muted-foreground">
                Tus anotaciones se guardan automáticamente
              </span>
            )}
            {resolvedType && (
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  resolvedType === 'PDF'
                    ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                    : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                }`}
              >
                {resolvedType}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {!loading && url && isAdmin() && (
              <Button variant="outline" size="sm" onClick={() => window.open(url, '_blank')}>
                <Download size={14} />
                <span className="ml-1">Descargar</span>
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={handleClose}>
              Cerrar
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
