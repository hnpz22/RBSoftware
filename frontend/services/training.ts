import { api } from '@/lib/api'
import type { TrainingProgram, TeacherProgramProgress, TrainingEnrollmentProgress } from '@/lib/types'

// ── Types (local to service) ────────────────────────────────────────────────

export interface TrainingModule {
  public_id: string
  title: string
  description: string | null
  order_index: number
  is_published: boolean
  created_at: string
  updated_at: string
}

export interface TrainingLesson {
  public_id: string
  title: string
  type: string
  content: string | null
  file_key: string | null
  duration_minutes: number | null
  order_index: number
  is_published: boolean
  created_at: string
  updated_at: string
}

export interface TrainingEvaluation {
  public_id: string
  title: string
  type: string
  description: string | null
  max_score: number
  passing_score: number
  is_published: boolean
  created_at: string
  updated_at: string
}

export interface QuizQuestion {
  public_id: string
  question: string
  options: { id: number; text: string }[]
  correct_option?: number
  points: number
  order_index: number
  created_at: string
  updated_at: string
}

export interface TrainingSubmission {
  public_id: string
  content: string | null
  file_name: string | null
  quiz_answers: Record<string, number> | null
  score: number | null
  feedback: string | null
  status: string
  submitted_at: string | null
  graded_at: string | null
  created_at: string
  updated_at: string
}

export interface TrainingEnrollment {
  public_id: string
  enrolled_at: string
  completed_at: string | null
  status: string
  created_at: string
  updated_at: string
}

export interface CompletionCheck {
  lessons_completed: number
  lessons_total: number
  evaluations_passed: number
  evaluations_total: number
  average_score: number
  is_eligible: boolean
}

// ── Programs ────────────────────────────────────────────────────────────────

export function listPrograms() {
  return api.get<TrainingProgram[]>('/training/programs')
}

export function getProgram(id: string) {
  return api.get<TrainingProgram>(`/training/programs/${id}`)
}

export function createProgram(data: {
  name: string
  description?: string | null
  objective?: string | null
  duration_hours?: number | null
}) {
  return api.post<TrainingProgram>('/training/programs', data)
}

export function updateProgram(id: string, data: Partial<TrainingProgram>) {
  return api.patch<TrainingProgram>(`/training/programs/${id}`, data)
}

export function publishProgram(id: string) {
  return api.post<void>(`/training/programs/${id}/publish`)
}

export function getProgramProgress(id: string) {
  return api.get<TrainingEnrollmentProgress[]>(`/training/programs/${id}/progress`)
}

export function getMyPrograms() {
  return api.get<TeacherProgramProgress[]>('/training/my-programs')
}

// ── Modules ─────────────────────────────────────────────────────────────────

export function listModules(programId: string) {
  return api.get<TrainingModule[]>(`/training/programs/${programId}/modules`)
}

export function createModule(programId: string, data: { title: string; description?: string | null; order_index?: number }) {
  return api.post<TrainingModule>(`/training/programs/${programId}/modules`, data)
}

export function updateModule(moduleId: string, data: Partial<TrainingModule>) {
  return api.patch<TrainingModule>(`/training/modules/${moduleId}`, data)
}

export function publishModule(moduleId: string) {
  return api.post<void>(`/training/modules/${moduleId}/publish`)
}

// ── Lessons ─────────────────────────────────────────────────────────────────

export function listLessons(moduleId: string) {
  return api.get<TrainingLesson[]>(`/training/modules/${moduleId}/lessons`)
}

export function createLesson(moduleId: string, formData: FormData) {
  return api.postForm<TrainingLesson>(`/training/modules/${moduleId}/lessons`, formData)
}

export function updateLesson(lessonId: string, data: Partial<TrainingLesson>) {
  return api.patch<TrainingLesson>(`/training/lessons/${lessonId}`, data)
}

export function completeLesson(lessonId: string) {
  return api.post<void>(`/training/lessons/${lessonId}/complete`)
}

export function getLessonViewUrl(lessonId: string) {
  return api.get<{ url: string }>(`/training/lessons/${lessonId}/view`)
}

// ── Evaluations ─────────────────────────────────────────────────────────────

export function listEvaluations(moduleId: string) {
  return api.get<TrainingEvaluation[]>(`/training/modules/${moduleId}/evaluations`)
}

export function createEvaluation(moduleId: string, data: { title: string; type: string; description?: string | null; max_score?: number; passing_score?: number }) {
  return api.post<TrainingEvaluation>(`/training/modules/${moduleId}/evaluations`, data)
}

export function updateEvaluation(evalId: string, data: Partial<TrainingEvaluation>) {
  return api.patch<TrainingEvaluation>(`/training/evaluations/${evalId}`, data)
}

// ── Quiz Questions ──────────────────────────────────────────────────────────

export function listQuestions(evaluationId: string) {
  return api.get<QuizQuestion[]>(`/training/evaluations/${evaluationId}/questions`)
}

export function createQuestion(evaluationId: string, data: { question: string; options: { id: number; text: string }[]; correct_option: number; points?: number; order_index?: number }) {
  return api.post<QuizQuestion>(`/training/evaluations/${evaluationId}/questions`, data)
}

export function deleteQuestion(questionId: string) {
  return api.delete<void>(`/training/questions/${questionId}`)
}

// ── Submissions ─────────────────────────────────────────────────────────────

export function submitQuiz(evaluationId: string, answers: Record<string, number>) {
  return api.post<TrainingSubmission>(`/training/evaluations/${evaluationId}/submit-quiz`, { answers })
}

export function submitPractical(evaluationId: string, formData: FormData) {
  return api.postForm<TrainingSubmission>(`/training/evaluations/${evaluationId}/submit-practical`, formData)
}

export function getMySubmission(evaluationId: string) {
  return api.get<TrainingSubmission>(`/training/evaluations/${evaluationId}/my-submission`)
}

export function listSubmissions(evaluationId: string) {
  return api.get<TrainingSubmission[]>(`/training/evaluations/${evaluationId}/submissions`)
}

export function gradeSubmission(submissionId: string, data: { score: number; feedback?: string | null }) {
  return api.post<void>(`/training/submissions/${submissionId}/grade`, data)
}

// ── Enrollments ─────────────────────────────────────────────────────────────

export function listEnrollments(programId: string) {
  return api.get<TrainingEnrollment[]>(`/training/programs/${programId}/enrollments`)
}

export function enrollTeacher(programId: string, userId: string) {
  return api.post<TrainingEnrollment>(`/training/programs/${programId}/enroll`, { user_id: userId })
}

// ── Certificates ────────────────────────────────────────────────────────────

export function checkCompletion(enrollmentId: string) {
  return api.get<CompletionCheck>(`/training/enrollments/${enrollmentId}/check`)
}

export function issueCertificate(enrollmentId: string) {
  return api.post<{ public_id: string; certificate_code: string }>(`/training/enrollments/${enrollmentId}/certificate`)
}
