'use client'

import { useEffect, useState } from 'react'
import { Eye, FileText, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import * as academicService from '@/services/academic'
import type { MySubmission, StudentAssignment } from '@/lib/types'
import { FileViewerModal } from '@/components/file-viewer-modal'
import { RubricEditor } from '@/components/rubric-editor'

interface Props {
  assignment: StudentAssignment
  submission: MySubmission | null
  onClose: () => void
  onSubmitted: () => void
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function detectFileType(file: File): 'PDF' | 'IMAGE' | null {
  if (file.type === 'application/pdf') return 'PDF'
  if (file.type.startsWith('image/')) return 'IMAGE'
  return null
}

function detectFileTypeFromName(name: string): 'PDF' | 'IMAGE' {
  const ext = name.split('.').pop()?.toLowerCase()
  if (ext && ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'].includes(ext)) return 'IMAGE'
  return 'PDF'
}

export function SubmitAssignmentModal({
  assignment,
  submission,
  onClose,
  onSubmitted,
}: Props) {
  const isGraded = submission?.status === 'GRADED'
  const [content, setContent] = useState(submission?.content ?? '')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [showLocalPreview, setShowLocalPreview] = useState(false)
  const [viewingSubmission, setViewingSubmission] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl)
    }
  }, [previewUrl])

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null
    setSelectedFile(file)

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }

    if (file) {
      setPreviewUrl(URL.createObjectURL(file))
    } else {
      setPreviewUrl(null)
    }
  }

  function clearFile() {
    setSelectedFile(null)
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
      setPreviewUrl(null)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await academicService.submitAssignment(
        assignment.public_id,
        content.trim() || null,
        selectedFile ?? undefined,
      )
      onSubmitted()
    } catch (err: any) {
      setError(err?.detail ?? 'Error al entregar')
    } finally {
      setSaving(false)
    }
  }

  const previewFileType = selectedFile ? detectFileType(selectedFile) : null

  return (
    <>
      {showLocalPreview && previewUrl && previewFileType && (
        <FileViewerModal
          isOpen={showLocalPreview}
          onClose={() => setShowLocalPreview(false)}
          localUrl={previewUrl}
          fileName={selectedFile!.name}
          fileType={previewFileType}
        />
      )}

      {viewingSubmission && submission?.file_name && (
        <FileViewerModal
          isOpen={viewingSubmission}
          onClose={() => setViewingSubmission(false)}
          submissionId={submission.public_id}
          fileName={submission.file_name}
          fileType={detectFileTypeFromName(submission.file_name)}
        />
      )}

      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <div className="w-full max-w-md rounded-lg border bg-card shadow-xl">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <h3 className="font-semibold">{assignment.title}</h3>
            <button onClick={onClose} className="rounded-md p-1 hover:bg-muted">
              <X size={16} />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-3 px-5 py-4">
            {assignment.description && (
              <p className="text-sm text-muted-foreground">
                {assignment.description}
              </p>
            )}

            <RubricEditor
              rubricEndpoint={`/academic/assignments/${assignment.public_id}/rubric`}
              canEdit={false}
            />

            {/* Existing submission info */}
            {submission && (
              <div className="rounded-md bg-muted/30 p-3 space-y-1">
                <p className="text-xs font-medium text-muted-foreground">
                  Entrega actual — {submission.status}
                </p>
                {submission.submitted_at && (
                  <p className="text-xs text-muted-foreground">
                    {new Date(submission.submitted_at).toLocaleString()}
                  </p>
                )}
                {submission.file_name && (
                  <div className="flex items-center gap-2 rounded-md border bg-muted/50 px-3 py-2 text-sm mt-2">
                    <FileText size={16} className="text-muted-foreground shrink-0" />
                    <span className="flex-1 truncate text-muted-foreground">
                      {submission.file_name}
                    </span>
                    <button
                      type="button"
                      onClick={() => setViewingSubmission(true)}
                      className="text-primary hover:underline text-xs shrink-0 flex items-center gap-1"
                    >
                      <Eye size={12} />
                      Ver mi entrega
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Graded feedback */}
            {isGraded && (
              <div className="rounded-md bg-green-500/10 p-3 space-y-1">
                <p className="text-sm font-medium text-green-700">
                  Puntaje: {submission!.score}/{assignment.max_score}
                </p>
                {submission!.feedback && (
                  <p className="text-sm text-green-700">
                    {submission!.feedback}
                  </p>
                )}
              </div>
            )}

            {/* Form fields (only if not graded) */}
            {!isGraded && (
              <>
                <div className="space-y-1">
                  <label className="text-xs font-medium">Respuesta</label>
                  <textarea
                    className="w-full min-h-[80px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                    placeholder="Escribe tu respuesta…"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-medium">
                    Archivo (opcional)
                  </label>
                  <input
                    type="file"
                    onChange={handleFileChange}
                    className="w-full text-sm"
                  />
                </div>

                {/* Selected file preview bar */}
                {selectedFile && (
                  <div className="flex items-center gap-2 rounded-md border bg-muted/50 px-3 py-2 text-sm">
                    <FileText size={16} className="text-muted-foreground shrink-0" />
                    <span className="flex-1 truncate">{selectedFile.name}</span>
                    <span className="text-muted-foreground shrink-0">
                      {formatFileSize(selectedFile.size)}
                    </span>
                    {previewFileType ? (
                      <button
                        type="button"
                        onClick={() => setShowLocalPreview(true)}
                        className="text-primary hover:underline text-xs shrink-0"
                      >
                        Vista previa
                      </button>
                    ) : (
                      <span className="text-xs text-muted-foreground shrink-0">
                        Sin vista previa
                      </span>
                    )}
                    <button
                      type="button"
                      onClick={clearFile}
                      className="text-destructive hover:text-destructive/80 shrink-0"
                    >
                      <X size={14} />
                    </button>
                  </div>
                )}
              </>
            )}

            {error && (
              <p className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {error}
              </p>
            )}

            <div className="flex justify-end gap-2 pt-1">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={onClose}
              >
                {isGraded ? 'Cerrar' : 'Cancelar'}
              </Button>
              {!isGraded && (
                <Button type="submit" size="sm" disabled={saving}>
                  {saving
                    ? 'Enviando…'
                    : submission
                      ? 'Actualizar entrega'
                      : 'Entregar'}
                </Button>
              )}
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
