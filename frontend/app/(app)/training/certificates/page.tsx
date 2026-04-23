'use client'

import { useEffect, useState } from 'react'
import { Award, Download, ExternalLink, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'

interface CertificateRaw {
  public_id: string
  program_public_id: string
  certificate_code: string
  badge_key: string | null
  issued_at: string
  created_at: string
  updated_at: string
}

interface VerifyData {
  valid: boolean
  certificate_code: string
  issued_at: string
  program_name: string | null
  holder: { first_name: string | null; last_name: string | null }
}

interface CertificateEnriched extends CertificateRaw {
  program_name: string
  teacher_name: string
}

async function generateBadge(cert: CertificateEnriched) {
  const canvas = document.createElement('canvas')
  canvas.width = 800
  canvas.height = 600
  const ctx = canvas.getContext('2d')!

  try {
    const templateData = await api.get<{ template_url: string | null }>(
      `/training/programs/${cert.program_public_id}/certificate-template`,
    )

    if (templateData.template_url) {
      await new Promise<void>((resolve, reject) => {
        const img = new Image()
        img.crossOrigin = 'anonymous'
        img.onload = () => {
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height)

          ctx.fillStyle = 'rgba(0, 0, 0, 0.35)'
          ctx.fillRect(0, 0, canvas.width, canvas.height)

          ctx.fillStyle = '#FFFFFF'
          ctx.font = 'bold 42px Arial, sans-serif'
          ctx.textAlign = 'center'
          ctx.shadowColor = 'rgba(0,0,0,0.5)'
          ctx.shadowBlur = 8
          ctx.fillText(cert.teacher_name, canvas.width / 2, 280)

          ctx.font = '24px Arial, sans-serif'
          ctx.fillStyle = '#FFD700'
          const programName =
            cert.program_name.length > 45
              ? cert.program_name.slice(0, 45) + '...'
              : cert.program_name
          ctx.fillText(programName, canvas.width / 2, 330)

          ctx.font = '16px Arial, sans-serif'
          ctx.fillStyle = 'rgba(255,255,255,0.8)'
          ctx.fillText(cert.certificate_code, canvas.width / 2, 380)

          ctx.shadowBlur = 0
          resolve()
        }
        img.onerror = reject
        img.src = templateData.template_url!
      })
    } else {
      canvas.width = 400
      canvas.height = 400

      ctx.fillStyle = '#1A237E'
      ctx.beginPath()
      ctx.arc(200, 200, 190, 0, Math.PI * 2)
      ctx.fill()

      ctx.fillStyle = '#FF6F00'
      ctx.beginPath()
      ctx.arc(200, 200, 160, 0, Math.PI * 2)
      ctx.fill()

      ctx.fillStyle = '#FFFFFF'
      ctx.font = 'bold 60px Arial'
      ctx.textAlign = 'center'
      ctx.fillText('RS', 200, 180)

      ctx.font = 'bold 20px Arial'
      ctx.fillText(cert.teacher_name, 200, 230)

      ctx.font = '14px Arial'
      ctx.fillStyle = '#FFD600'
      const pName =
        cert.program_name.length > 30
          ? cert.program_name.slice(0, 30) + '...'
          : cert.program_name
      ctx.fillText(pName, 200, 260)

      ctx.font = '12px Arial'
      ctx.fillStyle = '#FFFFFF'
      ctx.fillText(cert.certificate_code, 200, 300)
    }
  } catch {
    ctx.fillStyle = '#1A237E'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    ctx.fillStyle = '#FFFFFF'
    ctx.font = 'bold 24px Arial'
    ctx.textAlign = 'center'
    ctx.fillText(cert.teacher_name, canvas.width / 2, canvas.height / 2)
  }

  const link = document.createElement('a')
  link.download = `certificado-${cert.certificate_code}.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}

export default function CertificatesPage() {
  const [certs, setCerts] = useState<CertificateEnriched[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const rawCerts = await api.get<CertificateRaw[]>('/training/my-certificates')

      // Enrich each certificate with program name and holder name via verify endpoint
      const enriched = await Promise.all(
        rawCerts.map(async (cert) => {
          try {
            const verify = await api.get<VerifyData>(
              `/training/certificates/${cert.certificate_code}/verify`,
            )
            return {
              ...cert,
              program_name: verify.program_name ?? 'Programa',
              teacher_name: `${verify.holder.first_name ?? ''} ${verify.holder.last_name ?? ''}`.trim(),
            }
          } catch {
            return {
              ...cert,
              program_name: 'Programa',
              teacher_name: '',
            }
          }
        }),
      )
      setCerts(enriched)
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar certificados')
      setCerts([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Mis Certificados</h1>
          <p className="text-sm text-muted-foreground">
            {certs.length} certificado{certs.length !== 1 && 's'}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={load} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          <span className="ml-2">Actualizar</span>
        </Button>
      </div>

      {loading && (
        <p className="py-12 text-center text-muted-foreground">Cargando…</p>
      )}

      {!loading && error && (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-sm text-destructive">
          {error}
        </div>
      )}

      {!loading && !error && certs.length === 0 && (
        <p className="py-12 text-center text-muted-foreground">
          Aún no tienes certificados
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {certs.map((c) => (
          <div key={c.public_id} className="rounded-lg border bg-card p-5 space-y-4">
            {/* Badge preview */}
            <div className="flex justify-center">
              <div className="relative flex h-32 w-32 items-center justify-center rounded-full bg-[#FF6F00]"
                style={{ boxShadow: '0 0 0 12px #1A237E' }}
              >
                <div className="text-center">
                  <p className="text-2xl font-black text-white">RS</p>
                  <p className="mt-0.5 text-[8px] font-bold text-yellow-300 leading-tight">
                    {c.program_name.length > 20 ? c.program_name.slice(0, 20) + '…' : c.program_name}
                  </p>
                </div>
              </div>
            </div>

            {/* Info */}
            <div className="text-center">
              <p className="font-semibold">{c.program_name}</p>
              <p className="text-sm text-muted-foreground">{c.teacher_name}</p>
              <p className="mt-1 font-mono text-xs text-muted-foreground">{c.certificate_code}</p>
              <p className="text-xs text-muted-foreground">
                Emitido el{' '}
                {new Date(c.issued_at).toLocaleDateString('es-CO', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </p>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() => generateBadge(c)}
              >
                <Download size={13} className="mr-1" />
                Badge
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() =>
                  window.open(`/training/verify/${c.certificate_code}`, '_blank')
                }
              >
                <ExternalLink size={13} className="mr-1" />
                Verificar
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
