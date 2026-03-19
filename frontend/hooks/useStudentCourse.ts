import { useEffect, useState } from 'react'
import * as academicService from '@/services/academic'
import type { StudentUnitContent } from '@/lib/types'

export function useStudentCourse(courseId: string) {
  const [units, setUnits] = useState<StudentUnitContent[]>([])
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try {
      setUnits(await academicService.getStudentCourseContent(courseId))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [courseId])

  return { units, loading, reload: load }
}
