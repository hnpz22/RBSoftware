import { useEffect, useState } from 'react'
import * as academicService from '@/services/academic'
import type { GradeWithCourses, School } from '@/lib/types'

export function useSchoolDetail(schoolId: string) {
  const [school, setSchool] = useState<School | null>(null)
  const [grades, setGrades] = useState<GradeWithCourses[]>([])
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try {
      const [s, basicGrades] = await Promise.all([
        academicService.getSchool(schoolId),
        academicService.listGradesBySchool(schoolId),
      ])
      setSchool(s)

      // Enrich each grade with director + courses
      const enriched = await Promise.all(
        basicGrades.map((g) =>
          academicService.getGrade(g.public_id).catch(() => g),
        ),
      )
      setGrades(enriched)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [schoolId])

  return { school, setSchool, grades, loading, reload: load }
}
