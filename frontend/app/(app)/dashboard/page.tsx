'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import {
  BookOpen,
  CheckCircle,
  ClipboardList,
  Factory,
  GraduationCap,
  Layers,
  Package,
  ShoppingCart,
  TrendingUp,
  Users2,
  AlertTriangle,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ErrorBanner } from '@/components/error-banner'
import { api } from '@/lib/api'
import { useAuthStore } from '@/lib/store'
import type {
  CourseRead,
  Grade,
  GradeWithCourses,
  ProductionBatch,
  SalesOrder,
  StockAlert,
  StudentUnitContent,
} from '@/lib/types'

// ── StatCard ─────────────────────────────────────────────────────────────────

function StatCard({
  title,
  value,
  icon: Icon,
  sub,
  href,
  alert,
}: {
  title: string
  value: number | string
  icon: React.ElementType
  sub?: string
  href?: string
  alert?: boolean
}) {
  const content = (
    <Card
      className={`relative overflow-hidden ${
        alert && (value as number) > 0
          ? 'border-red-200 bg-red-50/50 dark:border-red-900 dark:bg-red-950/20'
          : ''
      }`}
    >
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${
        alert && (value as number) > 0 ? 'bg-accent' : 'bg-primary'
      }`} />
      <CardHeader className="flex flex-row items-center justify-between pb-2 pl-5">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <Icon
          size={18}
          className={
            alert && (value as number) > 0
              ? 'text-red-500'
              : 'text-muted-foreground'
          }
        />
      </CardHeader>
      <CardContent className="pl-5">
        <p
          className={`text-3xl font-bold ${alert && (value as number) > 0 ? 'text-red-600' : ''}`}
        >
          {value}
        </p>
        {sub && (
          <p className="mt-1 text-xs text-muted-foreground">{sub}</p>
        )}
        {href && (
          <p className="mt-2 text-xs text-primary underline-offset-2 hover:underline">
            Ver detalle →
          </p>
        )}
      </CardContent>
    </Card>
  )

  if (href) {
    return <Link href={href}>{content}</Link>
  }
  return content
}

// ── Role-specific panels ─────────────────────────────────────────────────────

function AdminPanel() {
  const [stats, setStats] = useState({
    pendingOrders: 0,
    approvedOrders: 0,
    activeBatches: 0,
    criticalStock: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [orders, batches, alerts] = await Promise.all([
        api.get<SalesOrder[]>('/commercial/orders'),
        api.get<ProductionBatch[]>('/production/batches'),
        api.get<StockAlert[]>('/inventory/alerts'),
      ])
      setStats({
        pendingOrders: orders.filter((o) => o.status === 'PENDING').length,
        approvedOrders: orders.filter((o) => o.status === 'APPROVED').length,
        activeBatches: batches.filter((b) =>
          ['PENDING', 'IN_PROGRESS'].includes(b.status),
        ).length,
        criticalStock: alerts.filter((a) => a.status_color === 'RED').length,
      })
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar el dashboard.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (loading) return <SkeletonCards count={4} />
  if (error) return <ErrorBanner message={error} onRetry={load} />

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <StatCard
        title="Órdenes Pendientes"
        value={stats.pendingOrders}
        icon={ShoppingCart}
        sub="Por aprobar"
      />
      <StatCard
        title="Órdenes Aprobadas"
        value={stats.approvedOrders}
        icon={TrendingUp}
        sub="Listas para producción"
      />
      <StatCard
        title="Batches Activos"
        value={stats.activeBatches}
        icon={Factory}
        sub="En producción"
      />
      <StatCard
        title="Stock Crítico"
        value={stats.criticalStock}
        icon={AlertTriangle}
        sub="Productos sin unidades FREE"
        href="/inventory?color=RED"
        alert
      />
    </div>
  )
}

function OperativoPanel() {
  const [stats, setStats] = useState({
    activeBatches: 0,
    criticalStock: 0,
    fulfillmentOrders: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [batches, alerts, orders] = await Promise.all([
        api.get<ProductionBatch[]>('/production/batches'),
        api.get<StockAlert[]>('/inventory/alerts'),
        api.get<SalesOrder[]>('/commercial/orders'),
      ])
      setStats({
        activeBatches: batches.filter((b) =>
          ['PENDING', 'IN_PROGRESS'].includes(b.status),
        ).length,
        criticalStock: alerts.filter((a) => a.status_color === 'RED').length,
        fulfillmentOrders: orders.filter(
          (o) => o.fulfillment_status === 'PACKING',
        ).length,
      })
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar el dashboard.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (loading) return <SkeletonCards count={3} />
  if (error) return <ErrorBanner message={error} onRetry={load} />

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
      <StatCard
        title="Batches Activos"
        value={stats.activeBatches}
        icon={Factory}
        sub="En producción"
        href="/production"
      />
      <StatCard
        title="Stock Crítico"
        value={stats.criticalStock}
        icon={AlertTriangle}
        sub="Productos sin unidades FREE"
        href="/inventory?color=RED"
        alert
      />
      <StatCard
        title="En Fulfillment"
        value={stats.fulfillmentOrders}
        icon={Package}
        sub="Órdenes en packing"
        href="/fulfillment"
      />
    </div>
  )
}

function ComercialPanel() {
  const [stats, setStats] = useState({
    pendingOrders: 0,
    approvedOrders: 0,
    todaySales: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const orders = await api.get<SalesOrder[]>('/commercial/orders')
      const today = new Date().toISOString().slice(0, 10)
      setStats({
        pendingOrders: orders.filter((o) => o.status === 'PENDING').length,
        approvedOrders: orders.filter((o) => o.status === 'APPROVED').length,
        todaySales: orders.filter(
          (o) => o.created_at.slice(0, 10) === today,
        ).length,
      })
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar el dashboard.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (loading) return <SkeletonCards count={3} />
  if (error) return <ErrorBanner message={error} onRetry={load} />

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
      <StatCard
        title="Órdenes Pendientes"
        value={stats.pendingOrders}
        icon={ShoppingCart}
        sub="Por aprobar"
        href="/orders"
      />
      <StatCard
        title="Órdenes Aprobadas"
        value={stats.approvedOrders}
        icon={TrendingUp}
        sub="Listas para producción"
      />
      <StatCard
        title="Ventas Hoy"
        value={stats.todaySales}
        icon={ShoppingCart}
        sub="Órdenes creadas hoy"
      />
    </div>
  )
}

function TeacherPanel() {
  const [stats, setStats] = useState({
    activeCourses: 0,
    pendingGrading: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const courses = await api.get<CourseRead[]>('/academic/my-courses')
      setStats((prev) => ({
        ...prev,
        activeCourses: courses.filter((c) => c.is_active).length,
      }))
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar el dashboard.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (loading) return <SkeletonCards count={2} />
  if (error) return <ErrorBanner message={error} onRetry={load} />

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
      <StatCard
        title="Mis Cursos Activos"
        value={stats.activeCourses}
        icon={BookOpen}
        sub="Cursos asignados"
        href="/academic/courses"
      />
      <StatCard
        title="Por Calificar"
        value={stats.pendingGrading}
        icon={ClipboardList}
        sub="Entregas pendientes de nota"
      />
    </div>
  )
}

function DirectorPanel() {
  const [stats, setStats] = useState({
    gradesCount: 0,
    totalStudents: 0,
    activeCourses: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const grades = await api.get<Grade[]>('/academic/my-grades')
      let totalStudents = 0
      let activeCourses = 0
      const details = await Promise.all(
        grades.map((g) =>
          api.get<GradeWithCourses>(`/academic/grades/${g.public_id}`),
        ),
      )
      for (const d of details) {
        activeCourses += d.courses.filter((c) => c.is_active).length
        const courseDetails = await Promise.all(
          d.courses.map((c) =>
            api
              .get<{ public_id: string }[]>(
                `/academic/courses/${c.public_id}/students`,
              )
              .catch(() => [] as { public_id: string }[]),
          ),
        )
        for (const students of courseDetails) {
          totalStudents += students.length
        }
      }
      setStats({
        gradesCount: grades.length,
        totalStudents,
        activeCourses,
      })
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar el dashboard.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (loading) return <SkeletonCards count={3} />
  if (error) return <ErrorBanner message={error} onRetry={load} />

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
      <StatCard
        title="Mis Grados"
        value={stats.gradesCount}
        icon={Layers}
        sub="Grados asignados"
        href="/academic/grades"
      />
      <StatCard
        title="Total Estudiantes"
        value={stats.totalStudents}
        icon={Users2}
        sub="En mis grados"
      />
      <StatCard
        title="Cursos Activos"
        value={stats.activeCourses}
        icon={BookOpen}
        sub="En mis grados"
      />
    </div>
  )
}

function StudentPanel() {
  const [stats, setStats] = useState({
    coursesCount: 0,
    pendingAssignments: 0,
    gradedThisWeek: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const courses = await api.get<CourseRead[]>('/academic/my-courses')
      let pending = 0
      let gradedWeek = 0
      const now = new Date()
      const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)

      const allContent = await Promise.all(
        courses.map((c) =>
          api
            .get<StudentUnitContent[]>(
              `/academic/courses/${c.public_id}/content`,
            )
            .catch(() => [] as StudentUnitContent[]),
        ),
      )

      for (const units of allContent) {
        for (const unit of units) {
          for (const a of unit.assignments) {
            if (!a.my_submission) {
              pending++
            } else if (
              a.my_submission.status === 'GRADED' &&
              a.my_submission.graded_at &&
              new Date(a.my_submission.graded_at) >= weekAgo
            ) {
              gradedWeek++
            }
          }
        }
      }

      setStats({
        coursesCount: courses.length,
        pendingAssignments: pending,
        gradedThisWeek: gradedWeek,
      })
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar el dashboard.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  if (loading) return <SkeletonCards count={3} />
  if (error) return <ErrorBanner message={error} onRetry={load} />

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
      <StatCard
        title="Mis Cursos"
        value={stats.coursesCount}
        icon={BookOpen}
        sub="Cursos matriculados"
        href="/academic/courses"
      />
      <StatCard
        title="Tareas Pendientes"
        value={stats.pendingAssignments}
        icon={ClipboardList}
        sub="Sin entregar"
        alert
      />
      <StatCard
        title="Calificadas esta Semana"
        value={stats.gradedThisWeek}
        icon={CheckCircle}
        sub="Últimos 7 días"
      />
    </div>
  )
}

// ── Skeleton ─────────────────────────────────────────────────────────────────

function SkeletonCards({ count }: { count: number }) {
  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i}>
          <CardContent className="p-6">
            <div className="h-10 animate-pulse rounded bg-muted" />
          </CardContent>
        </Card>
      ))}
    </div>
  )
}

// ── Helpers ──────────────────────────────────────────────────────────────────

const ROLE_SUBTITLES: Record<string, string> = {
  ADMIN: 'Panel de administración — RBSoftware',
  DIRECTOR: 'Panel de dirección académica',
  TEACHER: 'Panel docente',
  STUDENT: 'Tu espacio de aprendizaje',
  OPERATIVO: 'Panel operativo',
  COMERCIAL: 'Panel comercial',
}

function getSubtitle(roles: string[]): string {
  for (const role of [
    'ADMIN',
    'DIRECTOR',
    'TEACHER',
    'STUDENT',
    'OPERATIVO',
    'COMERCIAL',
  ]) {
    if (roles.includes(role)) return ROLE_SUBTITLES[role]
  }
  return 'Bienvenido'
}

function getPanelForRoles(roles: string[]) {
  if (roles.includes('ADMIN')) return <AdminPanel />
  if (roles.includes('OPERATIVO')) return <OperativoPanel />
  if (roles.includes('COMERCIAL')) return <ComercialPanel />
  if (roles.includes('DIRECTOR')) return <DirectorPanel />
  if (roles.includes('TEACHER')) return <TeacherPanel />
  if (roles.includes('STUDENT')) return <StudentPanel />
  return null
}

// ── Page ─────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const searchParams = useSearchParams()
  const unauthorizedError = searchParams.get('error') === 'unauthorized'
  const { user, roles } = useAuthStore()

  return (
    <div className="space-y-6">
      {unauthorizedError && (
        <div className="flex items-center justify-between gap-3 rounded-md border border-red-200 bg-red-50 px-4 py-3 dark:border-red-900 dark:bg-red-950/30">
          <p className="text-sm text-red-700 dark:text-red-400">
            No tienes permisos para acceder a esa sección. Si crees que esto es
            un error, cierra sesión y vuelve a ingresar.
          </p>
          <button
            onClick={async () => {
              await api.post('/auth/logout').catch(() => {})
              window.location.href = '/login'
            }}
            className="shrink-0 text-xs font-medium text-red-700 hover:underline dark:text-red-400"
          >
            Cerrar sesión →
          </button>
        </div>
      )}

      <div className="mb-2">
        <h1 className="text-2xl font-bold text-foreground">
          Bienvenido, {user?.first_name ?? ''} 👋
        </h1>
        <p className="text-muted-foreground mt-1">
          {getSubtitle(roles)}
        </p>
      </div>

      {getPanelForRoles(roles)}
    </div>
  )
}
