'use client'

import { useCourseDetail } from '@/hooks/useCourseDetail'
import { useAuthStore } from '@/lib/store'
import { TeacherCourseView } from './TeacherCourseView'
import { StudentCourseView } from './StudentCourseView'

interface Props {
  courseId: string
}

export function CourseDetailView({ courseId }: Props) {
  const { course, units, loading, reload } = useCourseDetail(courseId)
  const user = useAuthStore((s) => s.user)

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        Cargando…
      </div>
    )
  }

  if (!course) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        Curso no encontrado
      </div>
    )
  }

  const isTeacher = course.teacher.public_id === user?.public_id

  if (isTeacher) {
    return (
      <TeacherCourseView course={course} units={units} reload={reload} />
    )
  }

  return <StudentCourseView course={course} />
}
