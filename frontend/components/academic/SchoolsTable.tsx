'use client'

import type { School } from '@/lib/types'

interface Props {
  schools: School[]
  gradeCountMap: Record<string, number>
  loading: boolean
  onSelect: (school: School) => void
}

export function SchoolsTable({ schools, gradeCountMap, loading, onSelect }: Props) {
  return (
    <div className="rounded-lg border">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="px-4 py-3 text-left font-medium">Nombre</th>
            <th className="px-4 py-3 text-left font-medium">Ciudad</th>
            <th className="px-4 py-3 text-left font-medium">Grados activos</th>
            <th className="px-4 py-3 text-left font-medium">Activo</th>
          </tr>
        </thead>
        <tbody>
          {loading && (
            <tr>
              <td
                colSpan={4}
                className="px-4 py-8 text-center text-muted-foreground"
              >
                Cargando…
              </td>
            </tr>
          )}
          {!loading && schools.length === 0 && (
            <tr>
              <td
                colSpan={4}
                className="px-4 py-8 text-center text-muted-foreground"
              >
                No hay colegios registrados
              </td>
            </tr>
          )}
          {schools.map((s) => (
            <tr
              key={s.public_id}
              onClick={() => onSelect(s)}
              className="cursor-pointer border-b last:border-0 hover:bg-muted/30"
            >
              <td className="px-4 py-3 font-medium">{s.name}</td>
              <td className="px-4 py-3 text-muted-foreground">
                {s.city ?? <span className="text-xs italic">—</span>}
              </td>
              <td className="px-4 py-3 text-muted-foreground">
                {gradeCountMap[s.public_id] ?? 0}
              </td>
              <td className="px-4 py-3">
                <span
                  className={
                    s.is_active
                      ? 'text-green-600'
                      : 'text-muted-foreground'
                  }
                >
                  {s.is_active ? 'Sí' : 'No'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
