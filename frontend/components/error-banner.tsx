import { AlertCircle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ErrorBannerProps {
  message: string | null
  onRetry?: () => void
}

export function ErrorBanner({ message, onRetry }: ErrorBannerProps) {
  if (!message) return null

  return (
    <div className="flex items-start gap-3 rounded-lg border border-destructive/20 bg-destructive/10 px-4 py-3">
      <AlertCircle size={18} className="mt-0.5 shrink-0 text-destructive" />
      <p className="flex-1 text-sm text-destructive">{message}</p>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="shrink-0 border-destructive/30 text-destructive hover:bg-destructive/10"
        >
          <RefreshCw size={14} className="mr-1.5" />
          Reintentar
        </Button>
      )}
    </div>
  )
}
