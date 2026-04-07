'use client'

import { useParams } from 'next/navigation'
import { ProgramDetailView } from '@/components/training/ProgramDetailView'

export default function ProgramDetailPage() {
  const params = useParams()
  return <ProgramDetailView programId={params.id as string} />
}
