import { useEffect, useState } from 'react'
import * as academicService from '@/services/academic'
import type { CourseRead } from '@/lib/types'

export function useMyCourses() {
  const [courses, setCourses] = useState<CourseRead[]>([])
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try {
      setCourses(await academicService.getMyCourses())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return { courses, loading, reload: load }
}
