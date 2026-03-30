'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Plus, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useSchoolDetail } from '@/hooks/useSchoolDetail'
import { useAuthStore } from '@/lib/store'
import { GradesTable } from './GradesTable'
import { EditSchoolModal } from './EditSchoolModal'
import { CreateGradeModal } from './CreateGradeModal'
import { AssignDirectorModal } from './AssignDirectorModal'

interface Props {
  schoolId: string
}

export function SchoolDetailView({ schoolId }: Props) {
  const router = useRouter()
  const { school, setSchool, grades, loading, error, reload } =
    useSchoolDetail(schoolId)
  const { isAdmin } = useAuthStore()

  const [showEdit, setShowEdit] = useState(false)
  const [showCreateGrade, setShowCreateGrade] = useState(false)
  const [assigningGradeId, setAssigningGradeId] = useState<string | null>(null)

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        Cargando…
      </div>
    )
  }

  if (!loading && error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-sm text-destructive">
        {error}
      </div>
    )
  }

  if (!school) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        Colegio no encontrado
      </div>
    )
  }

  return (
    <>
      {showEdit && (
        <EditSchoolModal
          school={school}
          onClose={() => setShowEdit(false)}
          onSaved={(s) => {
            setSchool(s)
            setShowEdit(false)
          }}
        />
      )}
      {showCreateGrade && (
        <CreateGradeModal
          schoolId={schoolId}
          onClose={() => setShowCreateGrade(false)}
          onCreated={() => {
            setShowCreateGrade(false)
            reload()
          }}
        />
      )}
      {assigningGradeId && (
        <AssignDirectorModal
          gradeId={assigningGradeId}
          onClose={() => setAssigningGradeId(null)}
          onAssigned={() => {
            setAssigningGradeId(null)
            reload()
          }}
        />
      )}

      <div className="space-y-6">
        <div>
          <button
            onClick={() => router.push('/academic/schools')}
            className="mb-3 flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft size={14} /> Colegios
          </button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold">{school.name}</h1>
              {school.city && (
                <p className="text-sm text-muted-foreground">{school.city}</p>
              )}
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={reload}>
                <RefreshCw size={14} />
                <span className="ml-2">Actualizar</span>
              </Button>
              {isAdmin() && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowEdit(true)}
                >
                  Editar info
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Grados</h2>
            {isAdmin() && (
              <Button size="sm" onClick={() => setShowCreateGrade(true)}>
                <Plus size={14} />
                <span className="ml-2">Nuevo grado</span>
              </Button>
            )}
          </div>
          <GradesTable
            grades={grades}
            onSelectGrade={(id) => router.push(`/academic/grades/${id}`)}
            onAssignDirector={(id) => setAssigningGradeId(id)}
          />
        </div>
      </div>
    </>
  )
}
