import { useEffect, useState } from 'react'
import * as academicService from '@/services/academic'
import type { Grade } from '@/lib/types'

export function useMyGrades() {
  const [grades, setGrades] = useState<Grade[]>([])
  const [loading, setLoading] = useState(true)

  async function load() {
    setLoading(true)
    try {
      setGrades(await academicService.getMyGrades())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return { grades, loading, reload: load }
}
