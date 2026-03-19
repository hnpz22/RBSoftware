'use client'

import { useParams } from 'next/navigation'
import { SchoolDetailView } from '@/components/academic/SchoolDetailView'

export default function SchoolDetailPage() {
  const params = useParams()
  return <SchoolDetailView schoolId={params.id as string} />
}
