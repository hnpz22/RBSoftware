'use client'

import { useEffect, useRef, useState } from 'react'

const ADOBE_KEY = process.env.NEXT_PUBLIC_ADOBE_PDF_KEY ?? ''

export function AdobePDFViewer({
  url,
  fileName,
  height = '100%',
}: {
  url: string
  fileName: string
  height?: string
}) {
  const divId = useRef(`adobe-pdf-${Math.random().toString(36).slice(2)}`)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState(false)

  useEffect(() => {
    const checkReady = setInterval(() => {
      if (window.AdobeDC) {
        setReady(true)
        clearInterval(checkReady)
      }
    }, 100)

    const timeout = setTimeout(() => {
      clearInterval(checkReady)
      setError(true)
    }, 10000)

    return () => {
      clearInterval(checkReady)
      clearTimeout(timeout)
    }
  }, [])

  useEffect(() => {
    if (!ready || !url || !window.AdobeDC) return

    try {
      const viewer = new window.AdobeDC.View({
        clientId: ADOBE_KEY,
        divId: divId.current,
      })

      viewer.previewFile(
        {
          content: { location: { url } },
          metaData: { fileName: fileName || 'documento.pdf' },
        },
        {
          enableAnnotationAPIs: true,
          includePDFAnnotations: true,
          showAnnotationTools: true,
          defaultViewMode: 'FIT_PAGE',
          showDownloadPDF: false,
          showPrintPDF: false,
        },
      )
    } catch (err) {
      console.error('Adobe PDF error:', err)
      setError(true)
    }
  }, [ready, url, fileName])

  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 text-muted-foreground">
        <p className="text-sm">No se pudo cargar el visor de PDF</p>
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-primary hover:underline"
        >
          Abrir en nueva pestaña
        </a>
      </div>
    )
  }

  if (!ready) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-b-2 border-primary" />
      </div>
    )
  }

  return <div id={divId.current} style={{ height, width: '100%' }} />
}
