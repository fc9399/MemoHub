'use client'

import { useAuthStore } from '@/lib/stores/auth'
import { User, LogOut, Bell, Globe } from 'lucide-react'

export default function SettingsPage() {
  const { user, logout } = useAuthStore()

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Settings</h1>
          <p className="text-gray-500 mt-1">
            Manage your account settings and preferences
          </p>
        </div>
        <button
          onClick={logout}
          className="px-6 py-3 bg-red-100 text-red-700 rounded-2xl hover:bg-red-200 transition-colors font-medium flex items-center space-x-2"
        >
          <LogOut className="w-4 h-4" />
          <span>Logout</span>
        </button>
      </div>

      {/* Personal Info */}
      <div className="bg-white rounded-2xl shadow-brand p-6">
        <div className="flex items-center space-x-3 mb-6">
          <User className="w-5 h-5 text-gray-500" />
          <h2 className="text-lg font-semibold text-gray-900">Personal Information</h2>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Full Name
            </label>
            <input
              type="text"
              value={user?.name || ''}
              className="w-full px-3 py-2 border border-gray-300 rounded-2xl shadow-input focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
              readOnly
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              value={user?.email || ''}
              className="w-full px-3 py-2 border border-gray-300 rounded-2xl shadow-input focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
              readOnly
            />
          </div>
        </div>
      </div>

      {/* Preferences */}
      <div className="bg-white rounded-2xl shadow-brand p-6">
        <div className="flex items-center space-x-3 mb-6">
          <Bell className="w-5 h-5 text-gray-500" />
          <h2 className="text-lg font-semibold text-gray-900">Preferences</h2>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-gray-900">Email Notifications</h3>
              <p className="text-sm text-gray-500">Receive important updates and notifications</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-gray-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gray-900"></div>
            </label>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-gray-900">Auto Sync</h3>
              <p className="text-sm text-gray-500">Automatically sync integrated files</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" className="sr-only peer" defaultChecked />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-gray-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-gray-900"></div>
            </label>
          </div>
        </div>
      </div>

      {/* Language & Region */}
      <div className="bg-white rounded-2xl shadow-brand p-6">
        <div className="flex items-center space-x-3 mb-6">
          <Globe className="w-5 h-5 text-gray-500" />
          <h2 className="text-lg font-semibold text-gray-900">Language & Region</h2>
        </div>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Language
            </label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-2xl shadow-input focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent">
              <option value="zh-CN">Chinese (Simplified)</option>
              <option value="en-US">English</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Timezone
            </label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-2xl shadow-input focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent">
              <option value="Asia/Shanghai">Asia/Shanghai (UTC+8)</option>
              <option value="UTC">UTC (UTC+0)</option>
            </select>
          </div>
        </div>
      </div>

    </div>
  )
}
