'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { CheckCircle2, XCircle } from 'lucide-react'

interface VerifyResult {
  valid: boolean
  certificate_code: string
  issued_at: string
  program_name: string | null
  holder: { first_name: string | null; last_name: string | null }
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export default function VerifyCertificatePage() {
  const params = useParams()
  const code = params.code as string

  const [result, setResult] = useState<VerifyResult | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function verify() {
      try {
        const res = await fetch(`${API_BASE}/training/certificates/${code}/verify`)
        if (!res.ok) {
          setNotFound(true)
          return
        }
        setResult(await res.json())
      } catch {
        setNotFound(true)
      } finally {
        setLoading(false)
      }
    }
    verify()
  }, [code])

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        {/* Logo header */}
        <div className="mb-8 text-center">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-xl bg-[#1A237E]">
            <span className="text-xl font-black text-white">RS</span>
          </div>
          <h1 className="mt-3 text-xl font-bold text-gray-900">ROBOTSchool</h1>
          <p className="text-sm text-gray-500">Verificación de certificado</p>
        </div>

        {loading && (
          <div className="rounded-lg border bg-white p-8 text-center shadow-sm">
            <p className="text-gray-500">Verificando certificado…</p>
          </div>
        )}

        {!loading && notFound && (
          <div className="rounded-lg border border-red-200 bg-white p-8 text-center shadow-sm">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
              <XCircle size={32} className="text-red-600" />
            </div>
            <h2 className="text-lg font-semibold text-red-700">
              Certificado no encontrado
            </h2>
            <p className="mt-2 text-sm text-gray-500">
              El código <span className="font-mono font-medium">{code}</span> no
              corresponde a ningún certificado válido.
            </p>
          </div>
        )}

        {!loading && result && (
          <div className="rounded-lg border border-green-200 bg-white p-8 shadow-sm">
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                <CheckCircle2 size={32} className="text-green-600" />
              </div>
              <h2 className="text-lg font-semibold text-green-700">
                Certificado Válido
              </h2>
            </div>

            <div className="mt-6 space-y-4">
              <div className="rounded-md bg-gray-50 px-4 py-3">
                <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
                  Docente certificado
                </p>
                <p className="mt-1 text-lg font-semibold text-gray-900">
                  {result.holder.first_name} {result.holder.last_name}
                </p>
              </div>

              <div className="rounded-md bg-gray-50 px-4 py-3">
                <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
                  Programa completado
                </p>
                <p className="mt-1 font-medium text-gray-900">
                  {result.program_name}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-md bg-gray-50 px-4 py-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
                    Fecha de emisión
                  </p>
                  <p className="mt-1 text-sm font-medium text-gray-900">
                    {new Date(result.issued_at).toLocaleDateString('es-CO', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })}
                  </p>
                </div>
                <div className="rounded-md bg-gray-50 px-4 py-3">
                  <p className="text-xs font-medium uppercase tracking-wide text-gray-400">
                    Código único
                  </p>
                  <p className="mt-1 font-mono text-sm font-medium text-gray-900">
                    {result.certificate_code}
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-6 rounded-md bg-[#1A237E]/5 px-4 py-3 text-center">
              <p className="text-xs text-[#1A237E]">
                Este certificado fue emitido por{' '}
                <span className="font-semibold">ROBOTSchool Colombia</span>
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
