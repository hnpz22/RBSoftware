import { useEffect, useState } from 'react'
import * as academicService from '@/services/academic'
import type { CourseDetail, UnitRead } from '@/lib/types'

export function useCourseDetail(courseId: string) {
  const [course, setCourse] = useState<CourseDetail | null>(null)
  const [units, setUnits] = useState<UnitRead[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [c, u] = await Promise.all([
        academicService.getCourseDetail(courseId),
        academicService.listUnits(courseId),
      ])
      setCourse(c)
      setUnits(u)
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar curso')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [courseId])

  return { course, units, loading, error, reload: load }
}
