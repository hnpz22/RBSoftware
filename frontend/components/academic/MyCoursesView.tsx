'use client'

import { useRouter } from 'next/navigation'
import { BookOpen, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useMyCourses } from '@/hooks/useMyCourses'

export function MyCoursesView() {
  const router = useRouter()
  const { courses, loading, reload } = useMyCourses()

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Mis Cursos</h1>
          <p className="text-sm text-muted-foreground">
            {courses.length} cursos asignados
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

      {!loading && courses.length === 0 && (
        <p className="py-12 text-center text-muted-foreground">
          No tienes cursos asignados
        </p>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {courses.map((c) => (
          <div
            key={c.public_id}
            onClick={() => router.push(`/academic/courses/${c.public_id}`)}
            className="cursor-pointer rounded-lg border bg-card p-4 transition-colors hover:bg-muted/30"
          >
            <div className="flex items-center gap-2">
              <BookOpen size={16} className="text-muted-foreground" />
              <h3 className="font-medium">{c.name}</h3>
            </div>
            {c.description && (
              <p className="mt-1 text-sm text-muted-foreground line-clamp-2">
                {c.description}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
