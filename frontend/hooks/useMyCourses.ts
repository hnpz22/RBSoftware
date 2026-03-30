import { useEffect, useState } from 'react'
import * as academicService from '@/services/academic'
import type { MyCourseRead } from '@/lib/types'

export function useMyCourses() {
  const [courses, setCourses] = useState<MyCourseRead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      setCourses(await academicService.getMyCourses())
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar cursos')
      setCourses([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return { courses, loading, error, reload: load }
}
