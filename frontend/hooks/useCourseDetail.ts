import { useEffect, useState } from 'react'
import * as academicService from '@/services/academic'
import type { CourseDetail, UnitRead } from '@/lib/types'

export function useCourseDetail(courseId: string) {
  const [course, setCourse] = useState<CourseDetail | null>(null)
  const [units, setUnits] = useState<UnitRead[]>([])
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try {
      const [c, u] = await Promise.all([
        academicService.getCourseDetail(courseId),
        academicService.listUnits(courseId),
      ])
      setCourse(c)
      setUnits(u)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [courseId])

  return { course, units, loading, reload: load }
}
