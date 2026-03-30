import { api } from '@/lib/api'
import type {
  AssignmentRead,
  CourseDetail,
  CourseRead,
  Grade,
  GradeWithCourses,
  MaterialRead,
  MyCourseRead,
  School,
  StudentUnitContent,
  SubmissionWithStudent,
  UnitRead,
  User,
} from '@/lib/types'

// ── Schools ──────────────────────────────────────────────────────────────────

export function listSchools() {
  return api.get<School[]>('/academic/schools')
}

export function getSchool(id: string) {
  return api.get<School>(`/academic/schools/${id}`)
}

export function createSchool(data: {
  name: string
  city?: string | null
  address?: string | null
  contact_name?: string | null
  contact_email?: string | null
  contact_phone?: string | null
}) {
  return api.post<School>('/academic/schools', data)
}

export function updateSchool(
  id: string,
  data: Partial<{
    name: string
    city: string | null
    address: string | null
    contact_name: string | null
    contact_email: string | null
    contact_phone: string | null
  }>,
) {
  return api.patch<School>(`/academic/schools/${id}`, data)
}

// ── Grades ───────────────────────────────────────────────────────────────────

export function listGradesBySchool(schoolId: string) {
  return api.get<Grade[]>(`/academic/schools/${schoolId}/grades`)
}

export function getMyGrades() {
  return api.get<Grade[]>('/academic/my-grades')
}

export function getGrade(gradeId: string) {
  return api.get<GradeWithCourses>(`/academic/grades/${gradeId}`)
}

export function createGrade(
  schoolId: string,
  data: { name: string; description?: string | null },
) {
  return api.post<Grade>(
    `/academic/schools/${schoolId}/grades`,
    data,
  )
}

export function assignDirector(gradeId: string, userId: string) {
  return api.post(`/academic/grades/${gradeId}/director`, {
    user_id: userId,
  })
}

// ── Users (search) ───────────────────────────────────────────────────────────

export function listUsers() {
  return api.get<User[]>('/auth/users')
}

// ── Courses ──────────────────────────────────────────────────────────────────

export function getMyCourses() {
  return api.get<MyCourseRead[]>('/academic/my-courses')
}

export function getCourseDetail(courseId: string) {
  return api.get<CourseDetail>(`/academic/courses/${courseId}`)
}

export function listCoursesByGrade(gradeId: string) {
  return api.get<CourseRead[]>(`/academic/grades/${gradeId}/courses`)
}

export function createCourse(
  gradeId: string,
  data: { name: string; description?: string | null; teacher_id: string },
) {
  return api.post<CourseRead>(`/academic/grades/${gradeId}/courses`, data)
}

export function getCourseStudents(courseId: string) {
  return api.get<User[]>(`/academic/courses/${courseId}/students`)
}

export function enrollStudent(courseId: string, userId: string) {
  return api.post(`/academic/courses/${courseId}/students`, { user_id: userId })
}

export function transferStudent(
  studentId: string,
  fromCourseId: string,
  toCourseId: string,
) {
  return api.post(`/academic/students/${studentId}/transfer`, {
    from_course_id: fromCourseId,
    to_course_id: toCourseId,
  })
}

// ── Units ────────────────────────────────────────────────────────────────────

export function listUnits(courseId: string) {
  return api.get<UnitRead[]>(`/academic/courses/${courseId}/units`)
}

export function createUnit(
  courseId: string,
  data: { title: string; description?: string | null },
) {
  return api.post<UnitRead>(`/academic/courses/${courseId}/units`, data)
}

export function updateUnit(
  unitId: string,
  data: Partial<{ title: string; description: string | null }>,
) {
  return api.patch<UnitRead>(`/academic/units/${unitId}`, data)
}

export function publishUnit(unitId: string) {
  return api.post(`/academic/units/${unitId}/publish`)
}

export function unpublishUnit(unitId: string) {
  return api.delete(`/academic/units/${unitId}/publish`)
}

// ── Materials ────────────────────────────────────────────────────────────────

export function listMaterials(unitId: string) {
  return api.get<MaterialRead[]>(`/academic/units/${unitId}/materials`)
}

export function deleteMaterial(materialId: string) {
  return api.delete(`/academic/materials/${materialId}`)
}

export function publishMaterial(materialId: string) {
  return api.post(`/academic/materials/${materialId}/publish`)
}

export function unpublishMaterial(materialId: string) {
  return api.delete(`/academic/materials/${materialId}/publish`)
}

export function downloadMaterial(materialId: string) {
  return api.get<{ url: string }>(`/academic/materials/${materialId}/download`)
}

export function addMaterial(
  unitId: string,
  data: { title: string; type: string; content?: string | null },
  file?: File,
) {
  const form = new FormData()
  form.append('title', data.title)
  form.append('type', data.type)
  if (data.content) form.append('content', data.content)
  if (file) form.append('file', file)

  return api.postForm<MaterialRead>(
    `/academic/units/${unitId}/materials`,
    form,
  )
}

// ── Assignments ──────────────────────────────────────────────────────────────

export function listAssignments(unitId: string) {
  return api.get<AssignmentRead[]>(`/academic/units/${unitId}/assignments`)
}

export function createAssignment(
  unitId: string,
  data: {
    title: string
    description?: string | null
    due_date?: string | null
    max_score?: number
  },
) {
  return api.post<AssignmentRead>(
    `/academic/units/${unitId}/assignments`,
    data,
  )
}

export function publishAssignment(assignmentId: string) {
  return api.post(`/academic/assignments/${assignmentId}/publish`)
}

export function unpublishAssignment(assignmentId: string) {
  return api.delete(`/academic/assignments/${assignmentId}/publish`)
}

export function getAssignmentSubmissions(assignmentId: string) {
  return api.get<SubmissionWithStudent[]>(
    `/academic/assignments/${assignmentId}/submissions`,
  )
}

// ── Grading ──────────────────────────────────────────────────────────────────

export function gradeSubmission(
  submissionId: string,
  data: { score: number; feedback?: string | null },
) {
  return api.post(`/academic/submissions/${submissionId}/grade`, data)
}

// ── Student content ──────────────────────────────────────────────────────────

export function getStudentCourseContent(courseId: string) {
  return api.get<StudentUnitContent[]>(
    `/academic/courses/${courseId}/content`,
  )
}

export function submitAssignment(
  assignmentId: string,
  content?: string | null,
  file?: File,
) {
  const form = new FormData()
  if (content) form.append('content', content)
  if (file) form.append('file', file)

  return api.postForm(`/academic/assignments/${assignmentId}/submit`, form)
}
