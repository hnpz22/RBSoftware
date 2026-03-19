'use client'

import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import * as academicService from '@/services/academic'
import type { SubmissionWithStudent } from '@/lib/types'
import { GradeSubmissionModal } from './GradeSubmissionModal'

interface Props {
  assignmentId: string
  onClose: () => void
}

export function AssignmentDetailModal({ assignmentId, onClose }: Props) {
  const [submissions, setSubmissions] = useState<SubmissionWithStudent[]>([])
  const [loading, setLoading] = useState(true)
  const [gradingId, setGradingId] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    try {
      setSubmissions(
        await academicService.getAssignmentSubmissions(assignmentId),
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [assignmentId])

  const gradingSub = submissions.find((s) => s.public_id === gradingId)

  return (
    <>
      {gradingSub && (
        <GradeSubmissionModal
          submission={gradingSub}
          onClose={() => setGradingId(null)}
          onGraded={() => {
            setGradingId(null)
            load()
          }}
        />
      )}

      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
        <div className="w-full max-w-2xl rounded-lg border bg-card shadow-xl">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <h3 className="font-semibold">Entregas</h3>
            <button
              onClick={onClose}
              className="rounded-md p-1 hover:bg-muted"
            >
              <X size={16} />
            </button>
          </div>
          <div className="max-h-[60vh] overflow-y-auto px-5 py-4">
            {loading && (
              <p className="py-8 text-center text-muted-foreground">
                Cargando…
              </p>
            )}
            {!loading && submissions.length === 0 && (
              <p className="py-8 text-center text-muted-foreground">
                Sin entregas
              </p>
            )}
            {!loading && submissions.length > 0 && (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-3 py-2 text-left font-medium">
                      Estudiante
                    </th>
                    <th className="px-3 py-2 text-left font-medium">Estado</th>
                    <th className="px-3 py-2 text-left font-medium">
                      Puntaje
                    </th>
                    <th className="px-3 py-2 text-left font-medium">Fecha</th>
                    <th className="px-3 py-2 text-left font-medium"></th>
                  </tr>
                </thead>
                <tbody>
                  {submissions.map((s) => (
                    <tr key={s.public_id} className="border-b last:border-0">
                      <td className="px-3 py-2">
                        {s.student.first_name} {s.student.last_name}
                      </td>
                      <td className="px-3 py-2">
                        <Badge
                          variant={
                            s.status === 'GRADED' ? 'success' : 'warning'
                          }
                        >
                          {s.status}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {s.score ?? '—'}
                      </td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {s.submitted_at
                          ? new Date(s.submitted_at).toLocaleDateString()
                          : '—'}
                      </td>
                      <td className="px-3 py-2">
                        {s.status === 'SUBMITTED' && (
                          <Button
                            size="sm"
                            onClick={() => setGradingId(s.public_id)}
                          >
                            Calificar
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
          <div className="flex justify-end border-t px-5 py-3">
            <Button variant="outline" size="sm" onClick={onClose}>
              Cerrar
            </Button>
          </div>
        </div>
      </div>
    </>
  )
}
