"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BookOpen,
  Building2,
  Factory,
  GraduationCap,
  Layers,
  LayoutDashboard,
  LogOut,
  Package,
  PackageCheck,
  Plug,
  Shield,
  ShoppingCart,
  Users2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/store";

// ── Nav structure ─────────────────────────────────────────────────────────────

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  soon?: boolean;
  disabled?: boolean;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: "Operaciones",
    items: [
      { href: '/dashboard',   label: 'Dashboard',   icon: LayoutDashboard },
      { href: '/orders',      label: 'Órdenes',      icon: ShoppingCart },
      { href: '/catalog',     label: 'Catálogo',     icon: BookOpen },
      { href: '/inventory',   label: 'Inventario',   icon: Package },
      { href: '/production',  label: 'Producción',   icon: Factory },
      { href: '/fulfillment', label: 'Fulfillment',  icon: PackageCheck },
    ],
  },
  {
    title: "Académico",
    items: [
      { href: '/academic/schools', label: 'Colegios',   icon: Building2 },
      { href: '/academic/grades',  label: 'Mis Grados', icon: Layers },
      { href: '/academic/courses', label: 'Mis Cursos', icon: BookOpen },
    ],
  },
  {
    title: "Configuración",
    items: [
      { href: '/settings/users', label: 'Usuarios',          icon: Users2 },
      { href: '/settings/roles', label: 'Roles y Permisos',  icon: Shield },
    ],
  },
  {
    title: "Próximamente",
    items: [
      { href: '#', label: 'Administrativo', icon: GraduationCap, soon: true, disabled: true },
      { href: '#', label: 'Integraciones',  icon: Plug,          soon: true, disabled: true },
    ],
  },
];

// ── Component ─────────────────────────────────────────────────────────────────

export function Nav() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, setUser } = useAuthStore();

  async function handleLogout() {
    await api.post("/auth/logout").catch(() => {});
    setUser(null);
    router.push("/login");
  }

  return (
    <aside className="flex h-screen w-56 shrink-0 flex-col border-r bg-card">
      {/* Logo */}
      <div className="flex h-14 items-center border-b px-4">
        <span className="text-sm font-semibold tracking-wide">
          MIEL · RobotSchool
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {NAV_SECTIONS.map((section) => (
          <div key={section.title} className="mb-2">
            {/* Section title */}
            <p className="px-3 py-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {section.title}
            </p>

            {/* Items */}
            {section.items.map(
              ({ href, label, icon: Icon, soon, disabled }) => {
                const active =
                  !disabled &&
                  (pathname === href ||
                    (href !== "/" && pathname.startsWith(href + "/")));

                if (disabled) {
                  return (
                    <div
                      key={label}
                      className="flex cursor-not-allowed items-center gap-3 rounded-md px-3 py-2 text-sm opacity-40"
                    >
                      <Icon size={16} />
                      <span>{label}</span>
                      {soon && (
                        <span className="ml-auto rounded-sm bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
                          Soon
                        </span>
                      )}
                    </div>
                  );
                }

                return (
                  <Link
                    key={href}
                    href={href}
                    className={cn(
                      "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                      active
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    )}
                  >
                    <Icon size={16} />
                    <span>{label}</span>
                  </Link>
                );
              },
            )}
          </div>
        ))}
      </nav>

      {/* User + logout */}
      <div className="border-t p-3">
        {user && (
          <p className="mb-2 truncate px-1 text-xs text-muted-foreground">
            {user.first_name} {user.last_name}
          </p>
        )}
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <LogOut size={16} />
          Cerrar sesión
        </button>
      </div>
    </aside>
  );
}
