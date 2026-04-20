import { useEffect, useState } from 'react'
import * as academicService from '@/services/academic'
import type { Grade, GradeWithCourses, School } from '@/lib/types'

export function useSchoolDetail(schoolId: string) {
  const [school, setSchool] = useState<School | null>(null)
  const [grades, setGrades] = useState<GradeWithCourses[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [s, basicGrades] = await Promise.all([
        academicService.getSchool(schoolId),
        academicService.listGradesBySchool(schoolId),
      ])
      setSchool(s)

      const enriched = await Promise.all(
        basicGrades.map((g: Grade) =>
          academicService.getGrade(g.public_id).catch(() => ({
            ...g,
            school_public_id: schoolId,
            courses: [],
            director: null,
          } as GradeWithCourses)),
        ),
      )
      setGrades(enriched)
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar colegio')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [schoolId])

  return { school, setSchool, grades, loading, error, reload: load }
}
