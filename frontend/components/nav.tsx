'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  Award,
  BookOpen,
  BookOpenCheck,
  Building2,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  Factory,
  GraduationCap,
  Layers,
  LayoutDashboard,
  LogOut,
  Moon,
  Package,
  PackageCheck,
  Plug,
  Shield,
  ShoppingCart,
  Sun,
  Users2,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { api } from '@/lib/api'
import { useAuthStore, useSidebarStore, useThemeStore } from '@/lib/store'

// ── Nav structure ───────────────────────────────────────────────────────────

interface NavItem {
  href: string
  label: string
  icon: React.ElementType
  soon?: boolean
  disabled?: boolean
  visible?: () => boolean
}

interface NavSection {
  title: string
  items: NavItem[]
}

// ── Component ───────────────────────────────────────────────────────────────

export function Nav() {
  const pathname = usePathname()
  const router = useRouter()
  const { user, setUser, hasRole, isAdmin } = useAuthStore()
  const { open, collapsed, setOpen, toggleCollapsed } = useSidebarStore()
  const { theme, toggleTheme, syncFromSystem } = useThemeStore()

  const sections: NavSection[] = [
    {
      title: 'Operaciones',
      items: [
        { href: '/dashboard',   label: 'Dashboard',   icon: LayoutDashboard },
        { href: '/orders',      label: 'Órdenes',     icon: ShoppingCart,  visible: () => isAdmin() || hasRole('COMERCIAL') },
        { href: '/catalog',     label: 'Catálogo',    icon: BookOpen,      visible: () => isAdmin() || hasRole('COMERCIAL') },
        { href: '/inventory',   label: 'Inventario',  icon: Package,       visible: () => isAdmin() || hasRole('OPERATIVO') },
        { href: '/production',  label: 'Producción',  icon: Factory,       visible: () => isAdmin() || hasRole('OPERATIVO') },
        { href: '/fulfillment', label: 'Fulfillment', icon: PackageCheck,  visible: () => isAdmin() || hasRole('OPERATIVO') },
      ],
    },
    {
      title: 'Académico',
      items: [
        { href: '/academic/schools', label: 'Colegios',   icon: Building2, visible: () => isAdmin() },
        { href: '/academic/grades',  label: 'Mis Grados', icon: Layers,    visible: () => isAdmin() || hasRole('DIRECTOR') },
        { href: '/academic/courses', label: 'Mis Cursos', icon: BookOpen,  visible: () => isAdmin() || hasRole('DIRECTOR') || hasRole('TEACHER') || hasRole('STUDENT') },
      ],
    },
    {
      title: 'Capacitación',
      items: [
        {
          href: hasRole('TEACHER') && !isAdmin() && !hasRole('TRAINER') ? '/training/my-programs' : '/training/programs',
          label: 'Mis Programas',
          icon: BookOpenCheck,
          visible: () => isAdmin() || hasRole('TRAINER') || hasRole('TEACHER'),
        },
        { href: '/training/grading',      label: 'Calificaciones',   icon: ClipboardList, visible: () => isAdmin() || hasRole('TRAINER') },
        { href: '/training/certificates', label: 'Mis Certificados', icon: Award,         visible: () => hasRole('TEACHER') },
      ],
    },
    {
      title: 'Configuración',
      items: [
        { href: '/settings/users', label: 'Usuarios',         icon: Users2, visible: () => isAdmin() },
        { href: '/settings/roles', label: 'Roles y Permisos', icon: Shield, visible: () => isAdmin() },
      ],
    },
    {
      title: 'Próximamente',
      items: [
        { href: '#', label: 'Administrativo', icon: GraduationCap, soon: true, disabled: true },
        { href: '#', label: 'Integraciones',  icon: Plug,          soon: true, disabled: true },
      ],
    },
  ]

  const visibleSections = sections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => !item.visible || item.visible()),
    }))
    .filter((section) => section.items.length > 0)

  async function handleLogout() {
    await api.post('/auth/logout').catch(() => {})
    setUser(null)
    router.push('/login')
  }

  function handleNavClick() {
    if (typeof window !== 'undefined' && window.innerWidth < 768) {
      setOpen(false)
    }
  }

  const initials = user
    ? `${user.first_name?.[0] ?? ''}${user.last_name?.[0] ?? ''}`.toUpperCase()
    : ''

  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-50 flex flex-col border-r border-blue-800 bg-[#1A237E] transition-all duration-200',
        open ? 'translate-x-0' : '-translate-x-full',
        'md:translate-x-0',
        collapsed ? 'w-56 md:w-16' : 'w-56',
      )}
    >
      {/* Logo */}
      <div className="flex h-14 items-center border-b border-blue-800 px-4">
        {collapsed ? (
          <div className="hidden h-8 w-8 items-center justify-center rounded-lg bg-[#FF6F00] text-sm font-black text-white md:flex">
            RS
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#FF6F00] text-sm font-black text-white">
              RS
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-bold leading-tight text-white">RBSoftware</span>
              <span className="text-xs leading-tight text-blue-300">ROBOTSchool</span>
            </div>
          </div>
        )}
        <div className="flex items-center gap-2 md:hidden">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#FF6F00] text-sm font-black text-white">
            RS
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-bold leading-tight text-white">RBSoftware</span>
            <span className="text-xs leading-tight text-blue-300">ROBOTSchool</span>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {visibleSections.map((section) => (
          <div key={section.title} className="mb-2">
            {!collapsed ? (
              <p className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-blue-300">
                {section.title}
              </p>
            ) : (
              <div className="my-2 hidden border-t border-blue-800 md:block" />
            )}

            {section.items.map(({ href, label, icon: Icon, soon, disabled }) => {
              const active =
                !disabled &&
                (pathname === href ||
                  (href !== '/' && pathname.startsWith(href + '/')))

              if (disabled) {
                return (
                  <div
                    key={label}
                    className={cn(
                      'flex cursor-not-allowed items-center gap-3 rounded-md px-3 py-2 text-sm text-blue-400 opacity-60',
                      collapsed && 'md:justify-center md:px-0',
                    )}
                    title={collapsed ? label : undefined}
                  >
                    <Icon size={16} />
                    <span className={cn(collapsed && 'md:hidden')}>
                      {label}
                    </span>
                    {soon && !collapsed && (
                      <span className="ml-auto rounded-sm bg-blue-800 px-1.5 py-0.5 text-[10px] font-medium text-blue-300">
                        Soon
                      </span>
                    )}
                  </div>
                )
              }

              return (
                <Link
                  key={href}
                  href={href}
                  onClick={handleNavClick}
                  className={cn(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors',
                    active
                      ? 'bg-[#FF6F00] font-medium text-white'
                      : 'text-blue-100 hover:bg-blue-800 hover:text-white',
                    collapsed && 'md:justify-center md:px-0',
                  )}
                  title={collapsed ? label : undefined}
                >
                  <Icon size={16} />
                  <span className={cn(collapsed && 'md:hidden')}>
                    {label}
                  </span>
                </Link>
              )
            })}
          </div>
        ))}
      </nav>

      {/* User + logout + collapse toggle */}
      <div className="border-t border-blue-800 p-3">
        {user && (
          <div
            className={cn(
              'mb-2 flex items-center gap-2 px-1',
              collapsed && 'md:justify-center',
            )}
          >
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#FF6F00] text-xs font-bold text-white">
              {initials}
            </div>
            <div className={cn('min-w-0 flex-1', collapsed && 'md:hidden')}>
              <p className="truncate text-xs font-medium text-white">
                {user.first_name} {user.last_name}
              </p>
              <p className="truncate text-[10px] text-blue-300">{user.email}</p>
            </div>
          </div>
        )}
        <div className={cn(
          'flex items-center gap-1',
          collapsed && 'md:flex-col',
        )}>
          <button
            onClick={handleLogout}
            className={cn(
              'flex flex-1 items-center gap-2 rounded-md px-3 py-2 text-sm text-blue-100 transition-colors hover:bg-blue-800 hover:text-white',
              collapsed && 'md:justify-center md:px-0 md:flex-none',
            )}
            title={collapsed ? 'Cerrar sesión' : undefined}
          >
            <LogOut size={16} />
            <span className={cn(collapsed && 'md:hidden')}>Cerrar sesión</span>
          </button>
          <button
            onClick={toggleTheme}
            onDoubleClick={(e) => {
              e.preventDefault()
              localStorage.removeItem('theme')
              const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches
              syncFromSystem(systemDark ? 'dark' : 'light')
            }}
            className="rounded-md p-2 text-blue-300 transition-colors hover:bg-blue-800 hover:text-white"
            title="Clic: alternar tema · Doble clic: seguir tema del sistema"
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>

        <button
          onClick={toggleCollapsed}
          className="mt-2 hidden w-full items-center justify-center rounded-md py-2 text-blue-300 transition-colors hover:bg-blue-800 hover:text-white md:flex"
          title={collapsed ? 'Expandir sidebar' : 'Colapsar sidebar'}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
    </aside>
  )
}
