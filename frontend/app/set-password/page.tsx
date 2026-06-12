'use client'

import { Suspense, useEffect, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { api } from '@/lib/api'

type ValidateResponse = { valid: boolean; email?: string }

function SetPasswordForm() {
  const searchParams = useSearchParams()
  const token = searchParams.get('token')

  const [status, setStatus] = useState<'loading' | 'invalid' | 'ready' | 'done'>('loading')
  const [email, setEmail] = useState<string | null>(null)
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!token) {
      setStatus('invalid')
      return
    }
    api
      .get<ValidateResponse>(`/auth/password-reset/validate/${token}`)
      .then((res) => {
        if (res.valid) {
          setEmail(res.email ?? null)
          setStatus('ready')
        } else {
          setStatus('invalid')
        }
      })
      .catch(() => setStatus('invalid'))
  }, [token])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    if (password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres')
      return
    }
    if (password !== confirm) {
      setError('Las contraseñas no coinciden')
      return
    }
    setSaving(true)
    try {
      await api.post('/auth/password-reset/confirm', { token, new_password: password })
      setStatus('done')
    } catch (err: any) {
      setError(err?.detail ?? 'No se pudo establecer la contraseña')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <div className="w-full max-w-sm space-y-6 rounded-xl border bg-card p-8 shadow-sm">
        <div className="space-y-1">
          <h1 className="text-xl font-semibold">RobotSchool LMS</h1>
          <p className="text-sm text-muted-foreground">Establece tu contraseña de acceso</p>
        </div>

        {status === 'loading' && (
          <p className="text-sm text-muted-foreground">Verificando el enlace…</p>
        )}

        {status === 'invalid' && (
          <div className="space-y-4">
            <p className="rounded-md bg-destructive/10 px-3 py-3 text-sm text-destructive">
              Este enlace es inválido, expiró o ya fue usado.
            </p>
            <a
              href="/login"
              className="block w-full rounded-md bg-primary px-4 py-2 text-center text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Ir al inicio de sesión
            </a>
          </div>
        )}

        {status === 'ready' && (
          <form onSubmit={handleSubmit} className="space-y-4">
            {email && (
              <p className="text-sm text-muted-foreground">
                Cuenta: <span className="font-medium text-foreground">{email}</span>
              </p>
            )}
            <div className="space-y-1.5">
              <label htmlFor="password" className="text-sm font-medium">
                Nueva contraseña
              </label>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Mínimo 8 caracteres"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none ring-offset-background focus:ring-2 focus:ring-ring"
              />
            </div>
            <div className="space-y-1.5">
              <label htmlFor="confirm" className="text-sm font-medium">
                Confirmar contraseña
              </label>
              <input
                id="confirm"
                type="password"
                autoComplete="new-password"
                required
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="Repite la contraseña"
                className="w-full rounded-md border bg-background px-3 py-2 text-sm outline-none ring-offset-background focus:ring-2 focus:ring-ring"
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}

            <button
              type="submit"
              disabled={saving}
              className="w-full rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              {saving ? 'Guardando…' : 'Establecer contraseña'}
            </button>
          </form>
        )}

        {status === 'done' && (
          <div className="space-y-4">
            <p className="rounded-md bg-green-500/10 px-3 py-3 text-sm text-green-600">
              ¡Contraseña establecida! Ya puedes iniciar sesión.
            </p>
            <a
              href="/login"
              className="block w-full rounded-md bg-primary px-4 py-2 text-center text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              Ir al inicio de sesión
            </a>
          </div>
        )}
      </div>
    </div>
  )
}

export default function SetPasswordPage() {
  return (
    <Suspense fallback={null}>
      <SetPasswordForm />
    </Suspense>
  )
}
