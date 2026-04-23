'use client'

import { useEffect, useState } from 'react'
import { useAuthStore } from '@/lib/store'
import * as trainingService from '@/services/training'
import type { TrainingProgram } from '@/lib/types'
import type { TrainingModule } from '@/services/training'
import { AdminProgramView } from './AdminProgramView'
import { TeacherProgramView } from './TeacherProgramView'

interface Props {
  programId: string
}

export function ProgramDetailView({ programId }: Props) {
  const { isAdmin, hasRole } = useAuthStore()
  const [program, setProgram] = useState<TrainingProgram | null>(null)
  const [modules, setModules] = useState<TrainingModule[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [p, m] = await Promise.all([
        trainingService.getProgram(programId),
        trainingService.listModules(programId),
      ])
      setProgram(p)
      setModules(m)
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar programa')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [programId])

  if (loading) {
    return <div className="flex items-center justify-center py-20 text-muted-foreground">Cargando…</div>
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-sm text-destructive">
        {error}
      </div>
    )
  }

  if (!program) {
    return <div className="flex items-center justify-center py-20 text-muted-foreground">Programa no encontrado</div>
  }

  const canManage = isAdmin() || hasRole('TRAINER') || hasRole('SUPER_TRAINER')

  if (canManage) {
    return <AdminProgramView program={program} modules={modules} reload={load} />
  }

  return <TeacherProgramView program={program} modules={modules} reload={load} />
}
