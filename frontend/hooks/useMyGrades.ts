import { useEffect, useState } from 'react'
import * as academicService from '@/services/academic'
import type { Grade } from '@/lib/types'

export function useMyGrades() {
  const [grades, setGrades] = useState<Grade[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      setGrades(await academicService.getMyGrades())
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar grados')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return { grades, loading, error, reload: load }
}
