'use client'

import { useEffect, useRef, useState, useCallback } from 'react'
import {
  PdfLoader,
  PdfHighlighter,
  Highlight,
  Popup,
  AreaHighlight,
} from 'react-pdf-highlighter'
import type { IHighlight, NewHighlight, ScaledPosition } from 'react-pdf-highlighter'
import 'react-pdf-highlighter/dist/style.css'
import { api } from '@/lib/api'

const COLORS = [
  { label: 'Amarillo', value: '#FFD700' },
  { label: 'Verde', value: '#90EE90' },
  { label: 'Azul', value: '#87CEEB' },
  { label: 'Rosa', value: '#FFB6C1' },
]

const SAVE_DEBOUNCE_MS = 1500

interface Props {
  url: string
  materialId: string
  fileName: string
}

export function PDFHighlighterViewer({ url, materialId, fileName }: Props) {
  const [highlights, setHighlights] = useState<IHighlight[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedColor, setSelectedColor] = useState('#FFD700')
  const saveTimer = useRef<NodeJS.Timeout>()
  const scrollRef = useRef<(highlight: IHighlight) => void>()

  // Cargar highlights al montar
  useEffect(() => {
    api
      .get<{ highlights: IHighlight[] }>(
        `/academic/materials/${materialId}/annotations`,
      )
      .then((data) => {
        setHighlights(data.highlights ?? [])
      })
      .catch(() => setHighlights([]))
      .finally(() => setLoading(false))
  }, [materialId])

  // Guardar con debounce
  const saveHighlights = useCallback(
    (newHighlights: IHighlight[]) => {
      if (saveTimer.current) {
        clearTimeout(saveTimer.current)
      }
      saveTimer.current = setTimeout(() => {
        api
          .put(`/academic/materials/${materialId}/annotations`, {
            highlights: newHighlights,
          })
          .catch(console.error)
      }, SAVE_DEBOUNCE_MS)
    },
    [materialId],
  )

  // Agregar nuevo highlight
  function addHighlight(highlight: NewHighlight) {
    const newHighlight: IHighlight = {
      ...highlight,
      id: String(Math.random()).slice(2),
    }
    const updated = [...highlights, newHighlight]
    setHighlights(updated)
    saveHighlights(updated)
  }

  // Actualizar highlight existente
  function updateHighlight(
    id: string,
    position: Partial<ScaledPosition>,
    content: { text?: string; image?: string },
  ) {
    const updated = highlights.map((h) =>
      h.id === id ? { ...h, position: { ...h.position, ...position }, content } : h,
    )
    setHighlights(updated)
    saveHighlights(updated)
  }

  // Eliminar highlight
  function deleteHighlight(id: string) {
    const updated = highlights.filter((h) => h.id !== id)
    setHighlights(updated)
    saveHighlights(updated)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Barra de colores */}
      <div className="flex items-center gap-2 px-3 py-2 border-b bg-muted/30 text-xs text-muted-foreground">
        <span>Color:</span>
        {COLORS.map((c) => (
          <button
            key={c.value}
            title={c.label}
            onClick={() => setSelectedColor(c.value)}
            className={`w-5 h-5 rounded-full border-2 transition-transform hover:scale-110 ${
              selectedColor === c.value
                ? 'border-foreground scale-110'
                : 'border-transparent'
            }`}
            style={{ background: c.value }}
          />
        ))}
        <span className="ml-auto">
          {highlights.length} anotaci{highlights.length !== 1 ? 'ones' : 'on'}
        </span>
      </div>

      {/* Visor PDF */}
      <div className="flex-1 overflow-auto relative">
        <PdfLoader
          url={url}
          beforeLoad={
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          }
        >
          {(pdfDocument) => (
            <PdfHighlighter
              pdfDocument={pdfDocument}
              enableAreaSelection={(event) => event.altKey}
              onScrollChange={() => {}}
              scrollRef={(scrollTo) => {
                scrollRef.current = scrollTo
              }}
              onSelectionFinished={(
                position,
                content,
                hideTipAndSelection,
                _transformSelection,
              ) => (
                <CommentTip
                  color={selectedColor}
                  onConfirm={(comment) => {
                    addHighlight({ content, position, comment })
                    hideTipAndSelection()
                  }}
                  onCancel={hideTipAndSelection}
                />
              )}
              highlightTransform={(
                highlight,
                index,
                setTip,
                hideTip,
                _viewportToScaled,
                screenshot,
                isScrolledTo,
              ) => {
                const isArea = Boolean(highlight.content?.image)

                const component = isArea ? (
                  <AreaHighlight
                    isScrolledTo={isScrolledTo}
                    highlight={highlight}
                    onChange={(boundingRect) => {
                      updateHighlight(
                        highlight.id,
                        {
                          boundingRect,
                          pageNumber: highlight.position.pageNumber,
                        },
                        { image: screenshot(boundingRect) },
                      )
                    }}
                  />
                ) : (
                  <Highlight
                    isScrolledTo={isScrolledTo}
                    position={highlight.position}
                    comment={highlight.comment}
                  />
                )

                return (
                  <Popup
                    popupContent={
                      <HighlightPopup
                        highlight={highlight}
                        onDelete={() => {
                          deleteHighlight(highlight.id)
                          hideTip()
                        }}
                      />
                    }
                    onMouseOver={(popupContent) =>
                      setTip(highlight, () => popupContent)
                    }
                    onMouseOut={hideTip}
                    key={index}
                  >
                    {component}
                  </Popup>
                )
              }}
              highlights={highlights}
            />
          )}
        </PdfLoader>
      </div>
    </div>
  )
}

// Tip para agregar comentario al subrayar
function CommentTip({
  color,
  onConfirm,
  onCancel,
}: {
  color: string
  onConfirm: (comment: { text: string; emoji: string }) => void
  onCancel: () => void
}) {
  const [text, setText] = useState('')
  const [emoji, setEmoji] = useState('💡')

  return (
    <div className="bg-white rounded-lg shadow-lg border p-3 w-64 space-y-2">
      <div className="flex gap-1">
        {['💡', '❓', '⚠️', '✅', '📌'].map((e) => (
          <button
            key={e}
            onClick={() => setEmoji(e)}
            className={`text-lg rounded p-0.5 ${
              emoji === e ? 'bg-muted' : 'hover:bg-muted/50'
            }`}
          >
            {e}
          </button>
        ))}
      </div>
      <textarea
        placeholder="Comentario (opcional)"
        value={text}
        onChange={(e) => setText(e.target.value)}
        className="w-full text-sm border rounded p-2 resize-none h-16 focus:outline-none focus:ring-1 focus:ring-primary"
      />
      <div className="flex gap-2">
        <button
          onClick={() => onConfirm({ text, emoji })}
          className="flex-1 text-xs py-1.5 rounded font-medium text-white"
          style={{ background: color }}
        >
          Guardar
        </button>
        <button
          onClick={onCancel}
          className="flex-1 text-xs py-1.5 rounded border hover:bg-muted/50"
        >
          Cancelar
        </button>
      </div>
    </div>
  )
}

// Popup al hacer hover en highlight existente
function HighlightPopup({
  highlight,
  onDelete,
}: {
  highlight: IHighlight
  onDelete: () => void
}) {
  return (
    <div className="bg-white rounded-lg shadow-lg border p-2 max-w-xs">
      {highlight.comment?.text && (
        <p className="text-sm mb-2">
          {highlight.comment.emoji} {highlight.comment.text}
        </p>
      )}
      <button onClick={onDelete} className="text-xs text-destructive hover:underline">
        Eliminar anotación
      </button>
    </div>
  )
}
