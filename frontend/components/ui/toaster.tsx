'use client'

import { useEffect, useState } from 'react'
import { CheckCircle, X, XCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useToast, type Toast } from './use-toast'

// ── Single toast ────────────────────────────────────────────────────────────

function ToastItem({
  toast,
  onDismiss,
}: {
  toast: Toast
  onDismiss: (id: string) => void
}) {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const frame = requestAnimationFrame(() => setVisible(true))
    return () => cancelAnimationFrame(frame)
  }, [])

  const variantStyles = {
    default: 'border-border bg-card text-card-foreground',
    success:
      'border-green-200 bg-green-50 text-green-900 dark:border-green-800 dark:bg-green-950/60 dark:text-green-100',
    destructive:
      'border-red-200 bg-red-50 text-red-900 dark:border-red-800 dark:bg-red-950/60 dark:text-red-100',
  }

  const Icon =
    toast.variant === 'success'
      ? CheckCircle
      : toast.variant === 'destructive'
        ? XCircle
        : null

  return (
    <div
      className={cn(
        'pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-lg border p-4 shadow-lg transition-all duration-300',
        variantStyles[toast.variant],
        visible
          ? 'translate-y-0 opacity-100'
          : 'translate-y-2 opacity-0',
      )}
    >
      {Icon && (
        <Icon
          size={18}
          className={cn(
            'mt-0.5 shrink-0',
            toast.variant === 'success' && 'text-green-600 dark:text-green-400',
            toast.variant === 'destructive' && 'text-red-600 dark:text-red-400',
          )}
        />
      )}
      <div className="flex-1 space-y-0.5">
        <p className="text-sm font-semibold leading-tight">{toast.title}</p>
        {toast.description && (
          <p className="text-sm opacity-80">{toast.description}</p>
        )}
      </div>
      <button
        onClick={() => onDismiss(toast.id)}
        className="shrink-0 rounded-md p-0.5 opacity-60 hover:opacity-100"
      >
        <X size={14} />
      </button>
    </div>
  )
}

// ── Container ───────────────────────────────────────────────────────────────

export function Toaster() {
  const { toasts, dismiss } = useToast()

  if (toasts.length === 0) return null

  return (
    <div className="fixed inset-x-0 top-4 z-[100] mx-auto flex max-w-sm flex-col gap-2 px-4 sm:inset-x-auto sm:bottom-4 sm:right-4 sm:top-auto sm:mx-0 sm:px-0">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={dismiss} />
      ))}
    </div>
  )
}
