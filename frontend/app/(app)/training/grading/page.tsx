'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { ClipboardList, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import * as trainingService from '@/services/training'
import type { TrainingProgram } from '@/lib/types'

export default function GradingPage() {
  const router = useRouter()
  const [programs, setPrograms] = useState<TrainingProgram[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      setPrograms(await trainingService.listPrograms())
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar programas')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Calificaciones</h1>
          <p className="text-sm text-muted-foreground">Selecciona un programa para ver la planilla</p>
        </div>
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span className="ml-2">Actualizar</span>
        </Button>
      </div>

      {loading && <p className="py-12 text-center text-muted-foreground">Cargando…</p>}

      {!loading && error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-sm text-destructive">{error}</div>
      )}

      {!loading && !error && programs.length === 0 && (
        <p className="py-12 text-center text-muted-foreground">No hay programas</p>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {programs.map((p) => (
          <div
            key={p.public_id}
            onClick={() => router.push(`/training/grading/${p.public_id}`)}
            className="cursor-pointer rounded-lg border bg-card p-4 transition-colors hover:bg-muted/30"
          >
            <div className="flex items-center gap-3">
              <ClipboardList size={18} className="text-muted-foreground" />
              <div>
                <p className="font-medium">{p.name}</p>
                {p.duration_hours && (
                  <p className="text-xs text-muted-foreground">{p.duration_hours} horas</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
