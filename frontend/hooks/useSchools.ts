import { useEffect, useState } from 'react'
import * as academicService from '@/services/academic'
import type { Grade, School } from '@/lib/types'

export function useSchools() {
  const [schools, setSchools] = useState<School[]>([])
  const [gradeCountMap, setGradeCountMap] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const list = await academicService.listSchools()
      setSchools(list)

      const entries = await Promise.all(
        list.map((s) =>
          academicService
            .listGradesBySchool(s.public_id)
            .then((grades) => [
              s.public_id,
              grades.filter((g: Grade) => g.is_active).length,
            ] as const)
            .catch(() => [s.public_id, 0] as const),
        ),
      )
      setGradeCountMap(Object.fromEntries(entries))
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar colegios')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return { schools, gradeCountMap, loading, error, reload: load }
}
