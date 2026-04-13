import { useSyncExternalStore, useCallback } from 'react'

// ── Types ───────────────────────────────────────────────────────────────────

export interface Toast {
  id: string
  title: string
  description?: string
  variant: 'default' | 'success' | 'destructive'
  duration: number
}

type ToastInput = Omit<Toast, 'id' | 'duration'> & { duration?: number }

// ── Global store (module-scoped) ────────────────────────────────────────────

let toasts: Toast[] = []
const listeners = new Set<() => void>()

function emit() {
  listeners.forEach((l) => l())
}

let counter = 0

function addToast(input: ToastInput) {
  const id = String(++counter)
  const toast: Toast = { ...input, id, duration: input.duration ?? 3000 }
  toasts = [toast, ...toasts]
  emit()

  setTimeout(() => {
    dismissToast(id)
  }, toast.duration)
}

function dismissToast(id: string) {
  toasts = toasts.filter((t) => t.id !== id)
  emit()
}

function getSnapshot() {
  return toasts
}

function subscribe(listener: () => void) {
  listeners.add(listener)
  return () => listeners.delete(listener)
}

// ── Hook ────────────────────────────────────────────────────────────────────

export function useToast() {
  const currentToasts = useSyncExternalStore(subscribe, getSnapshot, getSnapshot)

  const toast = useCallback((input: ToastInput) => {
    addToast(input)
  }, [])

  const dismiss = useCallback((id: string) => {
    dismissToast(id)
  }, [])

  return { toasts: currentToasts, toast, dismiss }
}

// ── Standalone function (for use outside components) ────────────────────────

export const toast = addToast
