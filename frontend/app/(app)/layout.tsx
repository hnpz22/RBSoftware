import { Nav } from '@/components/nav'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden">
      <Nav />
      <main className="flex-1 overflow-y-auto bg-background p-6">{children}</main>
    </div>
  )
}
