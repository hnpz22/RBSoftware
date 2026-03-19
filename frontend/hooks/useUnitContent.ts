import { useEffect, useState } from 'react'
import * as academicService from '@/services/academic'
import type { AssignmentRead, MaterialRead } from '@/lib/types'

export function useUnitContent(unitId: string | null) {
  const [materials, setMaterials] = useState<MaterialRead[]>([])
  const [assignments, setAssignments] = useState<AssignmentRead[]>([])
  const [loading, setLoading] = useState(false)

  async function load() {
    if (!unitId) return
    setLoading(true)
    try {
      const [m, a] = await Promise.all([
        academicService.listMaterials(unitId),
        academicService.listAssignments(unitId),
      ])
      setMaterials(m)
      setAssignments(a)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (unitId) load()
    else {
      setMaterials([])
      setAssignments([])
    }
  }, [unitId])

  return { materials, assignments, loading, reload: load }
}
