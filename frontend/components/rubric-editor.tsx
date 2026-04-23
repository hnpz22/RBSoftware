'use client'

import { useEffect, useState } from 'react'
import { ClipboardList, Plus, Trash2 } from 'lucide-react'

import { api } from '@/lib/api'
import { toast } from '@/components/ui/use-toast'

interface RubricLevel {
  public_id?: string
  title: string
  description: string
  points: number
}

interface RubricCriteria {
  public_id?: string
  title: string
  description: string
  weight: number
  levels: RubricLevel[]
}

interface Rubric {
  title: string
  description: string
  criteria: RubricCriteria[]
}

interface RubricEditorProps {
  rubricEndpoint: string
  canEdit: boolean
  onSave?: () => void
}

const READONLY_LEVEL_COLORS = [
  'bg-green-50 dark:bg-green-950/30',
  'bg-blue-50 dark:bg-blue-950/30',
  'bg-yellow-50 dark:bg-yellow-950/30',
  'bg-red-50 dark:bg-red-950/30',
]

export function RubricEditor({
  rubricEndpoint,
  canEdit,
  onSave,
}: RubricEditorProps) {
  const [rubric, setRubric] = useState<Rubric | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    setLoading(true)
    api
      .get<Rubric | null>(rubricEndpoint)
      .then((data) => setRubric(data))
      .catch(() => setRubric(null))
      .finally(() => setLoading(false))
  }, [rubricEndpoint])

  function addCriteria() {
    setRubric((prev) => ({
      ...(prev ?? { title: '', description: '', criteria: [] }),
      criteria: [
        ...(prev?.criteria ?? []),
        {
          title: '',
          description: '',
          weight: 1,
          levels: [
            { title: 'Excelente', description: '', points: 4 },
            { title: 'Bueno', description: '', points: 3 },
            { title: 'Regular', description: '', points: 2 },
            { title: 'Insuficiente', description: '', points: 1 },
          ],
        },
      ],
    }))
  }

  function removeCriteria(ci: number) {
    setRubric((prev) =>
      prev
        ? { ...prev, criteria: prev.criteria.filter((_, i) => i !== ci) }
        : prev,
    )
  }

  function updateCriteria<K extends keyof RubricCriteria>(
    ci: number,
    key: K,
    value: RubricCriteria[K],
  ) {
    setRubric((prev) => {
      if (!prev) return prev
      const criteria = [...prev.criteria]
      criteria[ci] = { ...criteria[ci], [key]: value }
      return { ...prev, criteria }
    })
  }

  function updateLevel<K extends keyof RubricLevel>(
    ci: number,
    li: number,
    key: K,
    value: RubricLevel[K],
  ) {
    setRubric((prev) => {
      if (!prev) return prev
      const criteria = [...prev.criteria]
      const levels = [...criteria[ci].levels]
      levels[li] = { ...levels[li], [key]: value }
      criteria[ci] = { ...criteria[ci], levels }
      return { ...prev, criteria }
    })
  }

  function updateAllLevelTitles(li: number, value: string) {
    setRubric((prev) => {
      if (!prev) return prev
      return {
        ...prev,
        criteria: prev.criteria.map((c) => {
          const levels = [...c.levels]
          if (levels[li]) levels[li] = { ...levels[li], title: value }
          return { ...c, levels }
        }),
      }
    })
  }

  async function saveRubric() {
    if (!rubric) return
    setSaving(true)
    try {
      const updated = await api.put<Rubric>(rubricEndpoint, rubric)
      setRubric(updated)
      setEditing(false)
      onSave?.()
      toast({ title: 'Rúbrica guardada', variant: 'success' })
    } catch {
      toast({ title: 'Error al guardar', variant: 'destructive' })
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="text-sm text-muted-foreground py-6">
        Cargando rúbrica...
      </div>
    )
  }

  if (!rubric && !editing) {
    if (!canEdit) return null
    return (
      <div className="border-2 border-dashed rounded-xl p-8 text-center">
        <ClipboardList
          size={32}
          className="mx-auto text-muted-foreground mb-3"
        />
        <p className="text-sm font-medium mb-1">Sin rúbrica</p>
        <p className="text-xs text-muted-foreground mb-4">
          Define los criterios de evaluación
        </p>
        <button
          onClick={() => {
            setRubric({
              title: 'Rúbrica de evaluación',
              description: '',
              criteria: [],
            })
            setEditing(true)
          }}
          className="px-4 py-2 rounded-lg bg-primary text-white text-sm"
        >
          Crear rúbrica
        </button>
      </div>
    )
  }

  if (canEdit && editing && rubric) {
    return (
      <div>
        <div className="space-y-3 mb-6">
          <input
            placeholder="Título de la rúbrica"
            value={rubric.title}
            onChange={(e) =>
              setRubric((prev) =>
                prev ? { ...prev, title: e.target.value } : prev,
              )
            }
            className="w-full text-lg font-semibold border-b bg-transparent pb-1 focus:outline-none focus:border-primary"
          />
          <textarea
            placeholder="Descripción (opcional)"
            value={rubric.description}
            onChange={(e) =>
              setRubric((prev) =>
                prev ? { ...prev, description: e.target.value } : prev,
              )
            }
            className="w-full text-sm border rounded-lg p-2 resize-none h-16 bg-background"
          />
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="bg-muted">
                <th className="border p-3 text-left font-semibold min-w-[200px]">
                  Criterio
                </th>
                {rubric.criteria[0]?.levels.map((level, i) => (
                  <th
                    key={i}
                    className="border p-3 text-center font-semibold min-w-[150px]"
                  >
                    <input
                      value={level.title}
                      onChange={(e) =>
                        updateAllLevelTitles(i, e.target.value)
                      }
                      className="bg-transparent text-center w-full focus:outline-none"
                    />
                    <span className="block text-xs text-muted-foreground font-normal">
                      {level.points} pts
                    </span>
                  </th>
                ))}
                <th className="border p-2 w-8" />
              </tr>
            </thead>
            <tbody>
              {rubric.criteria.map((crit, ci) => (
                <tr key={ci} className="hover:bg-muted/30">
                  <td className="border p-3 align-top">
                    <input
                      placeholder="Nombre del criterio"
                      value={crit.title}
                      onChange={(e) =>
                        updateCriteria(ci, 'title', e.target.value)
                      }
                      className="w-full font-medium bg-transparent focus:outline-none mb-1"
                    />
                    <textarea
                      placeholder="Descripción..."
                      value={crit.description}
                      onChange={(e) =>
                        updateCriteria(ci, 'description', e.target.value)
                      }
                      className="w-full text-xs text-muted-foreground bg-transparent resize-none h-12 focus:outline-none"
                    />
                    <div className="flex items-center gap-1 mt-1">
                      <span className="text-xs text-muted-foreground">
                        Peso:
                      </span>
                      <input
                        type="number"
                        min="1"
                        max="10"
                        value={crit.weight}
                        onChange={(e) =>
                          updateCriteria(
                            ci,
                            'weight',
                            Number(e.target.value),
                          )
                        }
                        className="w-12 text-xs border rounded px-1 bg-background"
                      />
                    </div>
                  </td>

                  {crit.levels.map((level, li) => (
                    <td key={li} className="border p-3 align-top">
                      <textarea
                        placeholder="Descriptor..."
                        value={level.description}
                        onChange={(e) =>
                          updateLevel(ci, li, 'description', e.target.value)
                        }
                        className="w-full text-xs bg-transparent resize-none h-20 focus:outline-none"
                      />
                      <input
                        type="number"
                        min="0"
                        value={level.points}
                        onChange={(e) =>
                          updateLevel(
                            ci,
                            li,
                            'points',
                            Number(e.target.value),
                          )
                        }
                        className="w-16 text-xs border rounded px-1 bg-background mt-1"
                      />
                      <span className="text-xs text-muted-foreground ml-1">
                        pts
                      </span>
                    </td>
                  ))}

                  <td className="border p-2 align-top">
                    <button
                      onClick={() => removeCriteria(ci)}
                      className="p-1 rounded hover:bg-destructive/10 text-destructive"
                    >
                      <Trash2 size={14} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex justify-between mt-4">
          <button
            onClick={addCriteria}
            className="flex items-center gap-2 text-sm text-primary hover:underline"
          >
            <Plus size={14} />
            Agregar criterio
          </button>

          <div className="flex gap-2">
            <button
              onClick={() => setEditing(false)}
              className="px-4 py-2 rounded-lg border text-sm hover:bg-muted"
            >
              Cancelar
            </button>
            <button
              onClick={saveRubric}
              disabled={saving}
              className="px-4 py-2 rounded-lg bg-primary text-white text-sm font-medium disabled:opacity-50"
            >
              {saving ? 'Guardando...' : 'Guardar rúbrica'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  if (!rubric) return null

  return (
    <div>
      <div className="mb-4">
        <h3 className="text-lg font-semibold">{rubric.title}</h3>
        {rubric.description && (
          <p className="text-sm text-muted-foreground mt-1">
            {rubric.description}
          </p>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="bg-muted">
              <th className="border p-3 text-left font-semibold min-w-[200px]">
                Criterio
              </th>
              {rubric.criteria[0]?.levels.map((level, i) => (
                <th
                  key={i}
                  className={`border p-3 text-center font-semibold min-w-[150px] ${
                    READONLY_LEVEL_COLORS[i] ?? ''
                  }`}
                >
                  <span className="block">{level.title}</span>
                  <span className="block text-xs text-muted-foreground font-normal">
                    {level.points} pts
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rubric.criteria.map((crit, ci) => (
              <tr key={ci}>
                <td className="border p-3 align-top">
                  <p className="font-medium">{crit.title}</p>
                  {crit.description && (
                    <p className="text-xs text-muted-foreground mt-1">
                      {crit.description}
                    </p>
                  )}
                  <p className="text-xs text-muted-foreground mt-1">
                    Peso: {crit.weight}
                  </p>
                </td>
                {crit.levels.map((level, li) => (
                  <td
                    key={li}
                    className={`border p-3 align-top text-xs ${
                      READONLY_LEVEL_COLORS[li] ?? ''
                    }`}
                  >
                    {level.description || (
                      <span className="text-muted-foreground italic">
                        Sin descriptor
                      </span>
                    )}
                    <p className="mt-1 font-medium">{level.points} pts</p>
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {canEdit && (
        <div className="mt-4 flex justify-end">
          <button
            onClick={() => setEditing(true)}
            className="px-4 py-2 rounded-lg border text-sm hover:bg-muted"
          >
            Editar rúbrica
          </button>
        </div>
      )}
    </div>
  )
}
