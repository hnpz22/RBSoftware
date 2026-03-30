'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Plus, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useSchools } from '@/hooks/useSchools'
import { useAuthStore } from '@/lib/store'
import { SchoolsTable } from './SchoolsTable'
import { CreateSchoolModal } from './CreateSchoolModal'

export function SchoolsView() {
  const router = useRouter()
  const { schools, gradeCountMap, loading, error, reload } = useSchools()
  const { isAdmin } = useAuthStore()
  const [showCreate, setShowCreate] = useState(false)

  return (
    <>
      {showCreate && (
        <CreateSchoolModal
          onClose={() => setShowCreate(false)}
          onCreated={() => {
            setShowCreate(false)
            reload()
          }}
        />
      )}

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold">Colegios</h1>
            <p className="text-sm text-muted-foreground">
              {schools.length} colegios registrados
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={reload}
              disabled={loading}
            >
              <RefreshCw
                size={14}
                className={loading ? 'animate-spin' : ''}
              />
              <span className="ml-2">Actualizar</span>
            </Button>
            {isAdmin() && (
              <Button size="sm" onClick={() => setShowCreate(true)}>
                <Plus size={14} />
                <span className="ml-2">Nuevo colegio</span>
              </Button>
            )}
          </div>
        </div>

        {!loading && error && (
          <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-sm text-destructive">
            {error}
          </div>
        )}

        <SchoolsTable
          schools={schools}
          gradeCountMap={gradeCountMap}
          loading={loading}
          onSelect={(s) => router.push(`/academic/schools/${s.public_id}`)}
        />
      </div>
    </>
  )
}
