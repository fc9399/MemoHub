import { Sidebar } from '@/components/sidebar'
import { AuthGuard } from '@/components/auth-guard'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <AuthGuard>
      <div className="min-h-screen bg-gray-50 overflow-x-hidden">
        <div className="flex">
          <Sidebar />
          <main className="flex-1 overflow-x-hidden">
            <div className="p-8 overflow-x-hidden">
              {children}
            </div>
          </main>
        </div>
      </div>
    </AuthGuard>
  )
}
