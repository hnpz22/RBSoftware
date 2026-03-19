'use client'

import { useParams } from 'next/navigation'
import { CourseDetailView } from '@/components/academic/CourseDetailView'

export default function CourseDetailPage() {
  const params = useParams()
  return <CourseDetailView courseId={params.id as string} />
}
