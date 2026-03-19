'use client'

import { useRouter } from 'next/navigation'
import { Layers, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useMyGrades } from '@/hooks/useMyGrades'

export function MyGradesView() {
  const router = useRouter()
  const { grades, loading, reload } = useMyGrades()

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Mis Grados</h1>
          <p className="text-sm text-muted-foreground">
            {grades.length} grados asignados
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={reload} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span className="ml-2">Actualizar</span>
        </Button>
      </div>

      {loading && (
        <p className="py-12 text-center text-muted-foreground">Cargando…</p>
      )}

      {!loading && grades.length === 0 && (
        <p className="py-12 text-center text-muted-foreground">
          No tienes grados asignados
        </p>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {grades.map((g) => (
          <div
            key={g.public_id}
            onClick={() => router.push(`/academic/grades/${g.public_id}`)}
            className="cursor-pointer rounded-lg border bg-card p-4 transition-colors hover:bg-muted/30"
          >
            <div className="flex items-center gap-2">
              <Layers size={16} className="text-muted-foreground" />
              <h3 className="font-medium">{g.name}</h3>
            </div>
            {g.description && (
              <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                {g.description}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
