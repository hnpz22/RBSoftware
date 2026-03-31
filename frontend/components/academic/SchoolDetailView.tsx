'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Plus, RefreshCw, Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useSchoolDetail } from '@/hooks/useSchoolDetail'
import { useAuthStore } from '@/lib/store'
import { GradesTable } from './GradesTable'
import { EditSchoolModal } from './EditSchoolModal'
import { CreateGradeModal } from './CreateGradeModal'
import { AssignDirectorModal } from './AssignDirectorModal'
import * as academicService from '@/services/academic'
import type { User } from '@/lib/types'

interface Props {
  schoolId: string
}

type Tab = 'grades' | 'teachers'

export function SchoolDetailView({ schoolId }: Props) {
  const router = useRouter()
  const { school, setSchool, grades, loading, error, reload } =
    useSchoolDetail(schoolId)
  const { isAdmin } = useAuthStore()

  const [tab, setTab] = useState<Tab>('grades')
  const [showEdit, setShowEdit] = useState(false)
  const [showCreateGrade, setShowCreateGrade] = useState(false)
  const [assigningGradeId, setAssigningGradeId] = useState<string | null>(null)

  // Teachers state
  const [teachers, setTeachers] = useState<User[]>([])
  const [loadingTeachers, setLoadingTeachers] = useState(false)
  const [showAddTeacher, setShowAddTeacher] = useState(false)
  const [searchEmail, setSearchEmail] = useState('')
  const [searchResults, setSearchResults] = useState<User[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const [teacherError, setTeacherError] = useState<string | null>(null)

  async function loadTeachers() {
    setLoadingTeachers(true)
    try {
      const list = await academicService.listSchoolTeachers(schoolId)
      setTeachers(list)
    } catch {
      // ignore
    } finally {
      setLoadingTeachers(false)
    }
  }

  useEffect(() => {
    if (tab === 'teachers') loadTeachers()
  }, [tab, schoolId])

  async function handleSearch() {
    if (!searchEmail.trim()) return
    setSearchLoading(true)
    try {
      const all = await academicService.listUsers()
      const teacherIds = new Set(teachers.map((t) => t.public_id))
      const filtered = all.filter(
        (u) =>
          u.roles.includes('TEACHER') &&
          !teacherIds.has(u.public_id) &&
          (u.email.toLowerCase().includes(searchEmail.toLowerCase()) ||
            `${u.first_name} ${u.last_name}`
              .toLowerCase()
              .includes(searchEmail.toLowerCase())),
      )
      setSearchResults(filtered)
    } catch {
      // ignore
    } finally {
      setSearchLoading(false)
    }
  }

  async function handleAddTeacher(userId: string) {
    setTeacherError(null)
    try {
      await academicService.addSchoolTeacher(schoolId, userId)
      setShowAddTeacher(false)
      setSearchEmail('')
      setSearchResults([])
      await loadTeachers()
    } catch (err: any) {
      setTeacherError(err?.detail ?? 'Error al agregar docente')
    }
  }

  async function handleRemoveTeacher(userId: string) {
    setTeacherError(null)
    try {
      await academicService.removeSchoolTeacher(schoolId, userId)
      await loadTeachers()
    } catch (err: any) {
      setTeacherError(err?.detail ?? 'Error al remover docente')
    }
  }

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

  const tabs: { key: Tab; label: string }[] = [
    { key: 'grades', label: 'Grados' },
    { key: 'teachers', label: 'Docentes' },
  ]

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

      {/* Add Teacher Modal */}
      {showAddTeacher && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="w-full max-w-md rounded-lg border bg-background p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Agregar docente</h2>
              <button
                onClick={() => {
                  setShowAddTeacher(false)
                  setSearchEmail('')
                  setSearchResults([])
                  setTeacherError(null)
                }}
                className="text-muted-foreground hover:text-foreground"
              >
                <X size={18} />
              </button>
            </div>

            <div className="flex gap-2 mb-3">
              <Input
                placeholder="Buscar por nombre o email…"
                value={searchEmail}
                onChange={(e) => setSearchEmail(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
              <Button size="sm" onClick={handleSearch} disabled={searchLoading}>
                <Search size={14} />
              </Button>
            </div>

            {teacherError && (
              <p className="text-sm text-destructive mb-2">{teacherError}</p>
            )}

            {searchLoading && (
              <p className="text-sm text-muted-foreground py-4 text-center">
                Buscando…
              </p>
            )}

            {!searchLoading && searchResults.length === 0 && searchEmail && (
              <p className="text-sm text-muted-foreground py-4 text-center">
                No se encontraron docentes
              </p>
            )}

            {searchResults.length > 0 && (
              <div className="max-h-60 overflow-y-auto space-y-1">
                {searchResults.map((u) => (
                  <div
                    key={u.public_id}
                    className="flex items-center justify-between rounded-md border px-3 py-2 text-sm hover:bg-muted/30"
                  >
                    <div>
                      <p className="font-medium">
                        {u.first_name} {u.last_name}
                      </p>
                      <p className="text-xs text-muted-foreground">{u.email}</p>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleAddTeacher(u.public_id)}
                    >
                      Agregar
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
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

        {/* Tabs */}
        <div className="flex border-b">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2 text-sm font-medium border-b-2 ${
                tab === t.key
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Grades tab */}
        {tab === 'grades' && (
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
        )}

        {/* Teachers tab */}
        {tab === 'teachers' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Docentes</h2>
              {isAdmin() && (
                <Button size="sm" onClick={() => setShowAddTeacher(true)}>
                  <Plus size={14} />
                  <span className="ml-1">Agregar docente</span>
                </Button>
              )}
            </div>

            {teacherError && !showAddTeacher && (
              <p className="text-sm text-destructive">{teacherError}</p>
            )}

            <div className="rounded-lg border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-4 py-3 text-left font-medium">Nombre</th>
                    <th className="px-4 py-3 text-left font-medium">Email</th>
                    <th className="px-4 py-3 text-left font-medium">Activo</th>
                    {isAdmin() && (
                      <th className="px-4 py-3 text-left font-medium"></th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {loadingTeachers && (
                    <tr>
                      <td
                        colSpan={isAdmin() ? 4 : 3}
                        className="px-4 py-8 text-center text-muted-foreground"
                      >
                        Cargando…
                      </td>
                    </tr>
                  )}
                  {!loadingTeachers && teachers.length === 0 && (
                    <tr>
                      <td
                        colSpan={isAdmin() ? 4 : 3}
                        className="px-4 py-8 text-center text-muted-foreground"
                      >
                        No hay docentes asignados
                      </td>
                    </tr>
                  )}
                  {teachers.map((t) => (
                    <tr key={t.public_id} className="border-b last:border-0">
                      <td className="px-4 py-3 font-medium">
                        {t.first_name} {t.last_name}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {t.email}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={
                            t.is_active
                              ? 'text-green-600'
                              : 'text-muted-foreground'
                          }
                        >
                          {t.is_active ? 'Sí' : 'No'}
                        </span>
                      </td>
                      {isAdmin() && (
                        <td className="px-4 py-3">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleRemoveTeacher(t.public_id)}
                          >
                            Quitar
                          </Button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
