import { useEffect, useState } from 'react'
import * as academicService from '@/services/academic'
import type { StudentUnitContent } from '@/lib/types'

export function useStudentCourse(courseId: string) {
  const [units, setUnits] = useState<StudentUnitContent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      setUnits(await academicService.getStudentCourseContent(courseId))
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar contenido')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [courseId])

  return { units, loading, error, reload: load }
}
