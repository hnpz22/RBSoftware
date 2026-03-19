'use client'

import { useParams } from 'next/navigation'
import { GradeDetailView } from '@/components/academic/GradeDetailView'

export default function GradeDetailPage() {
  const params = useParams()
  return <GradeDetailView gradeId={params.id as string} />
}
