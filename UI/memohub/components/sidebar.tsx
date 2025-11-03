'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  Upload, 
  MessageSquare, 
  Key, 
  Plug, 
  Settings,
  ArrowRight
} from 'lucide-react'

const navigation = [
  { name: 'Uploads', href: '/dashboard', icon: Upload },
  { name: 'Chat', href: '/dashboard/chat', icon: MessageSquare },
  { name: 'API Keys', href: '/dashboard/api-keys', icon: Key },
  { name: 'Integrations', href: '/dashboard/integrations', icon: Plug },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <div className="w-64 bg-white border-r border-gray-200 min-h-screen">
      <div className="p-6">
        {/* Logo */}
        <Link href="/dashboard" className="flex items-center space-x-2 mb-8">
          <div className="w-8 h-8 bg-radial-brand rounded-lg flex items-center justify-center">
            <ArrowRight className="w-4 h-4 text-white rotate-45" />
          </div>
          <span className="text-xl font-extrabold text-gray-900">MemoHub</span>
        </Link>

        {/* Navigation */}
        <nav className="space-y-2">
          {navigation.map((item) => {
            const isActive = pathname === item.href
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center space-x-3 px-3 py-2 rounded-2xl text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-gray-100 text-gray-900'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <item.icon className="w-5 h-5" />
                <span>{item.name}</span>
              </Link>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
