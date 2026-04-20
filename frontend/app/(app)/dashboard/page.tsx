'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import {
  AlertTriangle,
  BookOpen,
  CheckCircle,
  ClipboardList,
  Factory,
  Layers,
  Package,
  ShoppingCart,
  TrendingDown,
  TrendingUp,
  Users2,
} from 'lucide-react'
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
  subtitle,
  icon: Icon,
  gradient,
  trend,
  href,
}: {
  title: string
  value: number | string
  subtitle: string
  icon: React.ElementType
  gradient: string
  trend?: { value: number; isPositive: boolean }
  href?: string
}) {
  const card = (
    <div
      className={`relative overflow-hidden rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 ${gradient}`}
    >
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-medium text-white/90">{title}</p>
        <div className="p-2 rounded-lg bg-white/20 backdrop-blur-sm">
          <Icon className="h-5 w-5 text-white" />
        </div>
      </div>
      <p className="text-3xl font-bold text-white">{value}</p>
      <p className="text-sm text-white/70 mt-1">{subtitle}</p>
      {trend && (
        <div className="inline-flex items-center gap-1 mt-3 px-2 py-1 rounded-full text-xs font-medium bg-white/20 text-white">
          {trend.isPositive ? (
            <TrendingUp className="h-3 w-3" />
          ) : (
            <TrendingDown className="h-3 w-3" />
          )}
          {trend.value}%
        </div>
      )}
    </div>
  )

  if (href) {
    return (
      <Link href={href} className="block">
        {card}
      </Link>
    )
  }
  return card
}

// ── Role-specific panels ─────────────────────────────────────────────────────

function AdminPanel() {
  const [stats, setStats] = useState({
    pendingOrders: 0,
    activeBatches: 0,
    criticalStock: 0,
    activeCourses: 0,
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
        activeBatches: batches.filter((b) =>
          ['PENDING', 'IN_PROGRESS'].includes(b.status),
        ).length,
        criticalStock: alerts.filter((a) => a.status_color === 'RED').length,
        activeCourses: 0,
      })
    } catch (err: any) {
      setError(err?.detail ?? 'Error al cargar el dashboard.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  if (loading) return <SkeletonCards count={4} />
  if (error) return <ErrorBanner message={error} onRetry={load} />

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <StatCard
        title="Pedidos Pendientes"
        value={stats.pendingOrders}
        subtitle="Órdenes por aprobar"
        icon={ShoppingCart}
        gradient="bg-gradient-to-br from-blue-500 to-blue-700"
      />
      <StatCard
        title="Lotes Activos"
        value={stats.activeBatches}
        subtitle="En producción"
        icon={Package}
        gradient="bg-gradient-to-br from-orange-500 to-orange-700"
      />
      <StatCard
        title="Stock Crítico"
        value={stats.criticalStock}
        subtitle="Productos sin unidades FREE"
        icon={AlertTriangle}
        gradient="bg-gradient-to-br from-green-500 to-green-700"
        href="/inventory?color=RED"
      />
      <StatCard
        title="Cursos Activos"
        value={stats.activeCourses}
        subtitle="Cursos en el sistema"
        icon={BookOpen}
        gradient="bg-gradient-to-br from-purple-500 to-purple-700"
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

  useEffect(() => {
    load()
  }, [])

  if (loading) return <SkeletonCards count={3} />
  if (error) return <ErrorBanner message={error} onRetry={load} />

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <StatCard
        title="Lotes Activos"
        value={stats.activeBatches}
        subtitle="En producción"
        icon={Factory}
        gradient="bg-gradient-to-br from-orange-500 to-orange-700"
        href="/production"
      />
      <StatCard
        title="Stock Crítico"
        value={stats.criticalStock}
        subtitle="Productos sin unidades FREE"
        icon={AlertTriangle}
        gradient="bg-gradient-to-br from-green-500 to-green-700"
        href="/inventory?color=RED"
      />
      <StatCard
        title="En Fulfillment"
        value={stats.fulfillmentOrders}
        subtitle="Órdenes en packing"
        icon={Package}
        gradient="bg-gradient-to-br from-cyan-500 to-cyan-700"
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

  useEffect(() => {
    load()
  }, [])

  if (loading) return <SkeletonCards count={3} />
  if (error) return <ErrorBanner message={error} onRetry={load} />

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <StatCard
        title="Órdenes Pendientes"
        value={stats.pendingOrders}
        subtitle="Por aprobar"
        icon={ShoppingCart}
        gradient="bg-gradient-to-br from-blue-500 to-blue-700"
        href="/orders"
      />
      <StatCard
        title="Órdenes Aprobadas"
        value={stats.approvedOrders}
        subtitle="Listas para producción"
        icon={TrendingUp}
        gradient="bg-gradient-to-br from-emerald-500 to-emerald-700"
      />
      <StatCard
        title="Ventas Hoy"
        value={stats.todaySales}
        subtitle="Órdenes creadas hoy"
        icon={ShoppingCart}
        gradient="bg-gradient-to-br from-indigo-500 to-indigo-700"
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

  useEffect(() => {
    load()
  }, [])

  if (loading) return <SkeletonCards count={2} />
  if (error) return <ErrorBanner message={error} onRetry={load} />

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <StatCard
        title="Mis Cursos Activos"
        value={stats.activeCourses}
        subtitle="Cursos asignados"
        icon={BookOpen}
        gradient="bg-gradient-to-br from-blue-500 to-blue-700"
        href="/academic/courses"
      />
      <StatCard
        title="Por Calificar"
        value={stats.pendingGrading}
        subtitle="Entregas pendientes de nota"
        icon={ClipboardList}
        gradient="bg-gradient-to-br from-amber-500 to-amber-700"
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

  useEffect(() => {
    load()
  }, [])

  if (loading) return <SkeletonCards count={3} />
  if (error) return <ErrorBanner message={error} onRetry={load} />

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <StatCard
        title="Mis Grados"
        value={stats.gradesCount}
        subtitle="Grados asignados"
        icon={Layers}
        gradient="bg-gradient-to-br from-purple-500 to-purple-700"
        href="/academic/grades"
      />
      <StatCard
        title="Total Estudiantes"
        value={stats.totalStudents}
        subtitle="En mis grados"
        icon={Users2}
        gradient="bg-gradient-to-br from-pink-500 to-pink-700"
      />
      <StatCard
        title="Cursos Activos"
        value={stats.activeCourses}
        subtitle="En mis grados"
        icon={BookOpen}
        gradient="bg-gradient-to-br from-blue-500 to-blue-700"
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

  useEffect(() => {
    load()
  }, [])

  if (loading) return <SkeletonCards count={3} />
  if (error) return <ErrorBanner message={error} onRetry={load} />

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      <StatCard
        title="Mis Cursos"
        value={stats.coursesCount}
        subtitle="Cursos matriculados"
        icon={BookOpen}
        gradient="bg-gradient-to-br from-blue-500 to-blue-700"
        href="/academic/courses"
      />
      <StatCard
        title="Tareas Pendientes"
        value={stats.pendingAssignments}
        subtitle="Sin entregar"
        icon={ClipboardList}
        gradient="bg-gradient-to-br from-rose-500 to-rose-700"
      />
      <StatCard
        title="Calificadas esta Semana"
        value={stats.gradedThisWeek}
        subtitle="Últimos 7 días"
        icon={CheckCircle}
        gradient="bg-gradient-to-br from-emerald-500 to-emerald-700"
      />
    </div>
  )
}

// ── Skeleton ─────────────────────────────────────────────────────────────────

function SkeletonCards({ count }: { count: number }) {
  const cols =
    count === 2
      ? 'lg:grid-cols-2'
      : count === 3
        ? 'lg:grid-cols-3'
        : 'lg:grid-cols-4'
  return (
    <div className={`grid grid-cols-1 sm:grid-cols-2 ${cols} gap-6`}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="h-36 rounded-xl bg-muted animate-pulse" />
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

      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-bold text-foreground">
            Bienvenido, {user?.first_name ?? ''} 👋
          </h1>
          <p className="text-muted-foreground mt-1">{getSubtitle(roles)}</p>
        </div>
      </div>

      {getPanelForRoles(roles)}
    </div>
  )
}
