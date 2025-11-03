'use client'

import Link from 'next/link'
import { ArrowRight, Menu, Mail, Send } from 'lucide-react'
import { useState } from 'react'

export default function ContactPage() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="flex min-h-screen">
      {/* Left sidebar navigation */}
      <aside className={`fixed top-0 left-0 h-full flex flex-col justify-between py-8 transition-all duration-300 ${
        sidebarOpen 
          ? 'w-64 px-6 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800' 
          : 'w-0 px-0 bg-transparent border-r-0'
      }`}>
        <div>
          <div className="mb-12">
            <Link 
              href="/"
              className={`text-xl font-bold text-black font-display transition-all duration-300 hover:opacity-80 flex items-center space-x-3 ${
                sidebarOpen ? 'opacity-100' : 'opacity-0'
              }`}
            >
              <div className="w-8 h-8 bg-radial-brand rounded-lg flex items-center justify-center">
                <ArrowRight className="w-4 h-4 text-white rotate-45" />
              </div>
              <span className={sidebarOpen ? 'block' : 'hidden'}>MemoHub</span>
            </Link>
          </div>
          
          <nav>
            <ul className="space-y-4">
              <li>
                <Link 
                  className={`text-gray-800 dark:text-gray-200 nav-link-hover transition-all duration-200 ${
                    sidebarOpen ? 'block' : 'hidden'
                  }`} 
                  href="/#about"
                >
                  About
                </Link>
              </li>
              <li>
                <Link className={`text-gray-800 dark:text-gray-200 nav-link-hover transition-all duration-200 ${
                  sidebarOpen ? 'block' : 'hidden'
                }`} href="/contact">
                  Contact Us
                </Link>
              </li>
            </ul>
          </nav>
        </div>
      </aside>

      {/* Floating open button - only visible when collapsed */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="fixed top-4 left-4 z-50 p-3 bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        >
          <Menu className="w-5 h-5 text-gray-600 dark:text-gray-400" />
        </button>
      )}

      {/* Main content area */}
      <main className={`flex-1 flex flex-col transition-all duration-300 ${
        sidebarOpen ? 'ml-64' : 'ml-0'
      }`}>
        {/* Upper part: gradient background */}
        <section className="h-[45vh] w-full flex items-center justify-center p-8 gradient-bg relative overflow-hidden">
          {/* Decorative background elements */}
          <div className="absolute inset-0 opacity-5">
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-white rounded-full blur-3xl"></div>
            <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-white rounded-full blur-3xl"></div>
          </div>
          
          <div className="w-full max-w-5xl text-center relative z-10">
            <h1 className="text-6xl lg:text-8xl font-extrabold text-white mb-6" style={{ textShadow: '0 4px 20px rgba(0, 0, 0, 0.3), 0 2px 10px rgba(0, 0, 0, 0.2)' }}>
              Contact Us
            </h1>
            <p className="text-xl font-light text-white/95 tracking-wide">We'd love to hear from you</p>
          </div>
        </section>

        {/* Lower part: white background */}
        <section className="w-full flex-grow p-20 bg-white">
          <div className="max-w-6xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-16">
              {/* Contact information */}
              <div className="space-y-8">
                <div>
                  <h2 className="text-4xl font-extrabold text-gray-900 mb-4 tracking-tight">Get in Touch</h2>
                  <div className="w-16 h-1 bg-gradient-to-r from-orange-400 to-orange-600 rounded-full"></div>
                </div>
                <p className="text-gray-700 text-lg leading-relaxed font-light">
                  Have questions, feedback, or need support? We're here to help. 
                  Reach out to us via email and we'll get back to you as soon as possible.
                </p>
                
                <div className="pt-4">
                  <a
                    href="mailto:yulanqiao@outlook.com"
                    className="group inline-flex items-center space-x-3 bg-gray-900 text-white px-10 py-5 rounded-2xl font-semibold hover:bg-gray-800 transition-all duration-300 shadow-xl hover:shadow-2xl hover:scale-105"
                  >
                    <Mail className="w-5 h-5 transition-transform group-hover:scale-110" />
                    <span className="tracking-wide">yulanqiao@outlook.com</span>
                    <Send className="w-5 h-5 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition-all duration-300" />
                  </a>
                </div>
              </div>

              {/* Additional information */}
              <div className="space-y-8">
                <div>
                  <h3 className="text-4xl font-extrabold text-gray-900 mb-4 tracking-tight">Why Contact Us?</h3>
                  <div className="w-16 h-1 bg-gradient-to-r from-orange-400 to-orange-600 rounded-full"></div>
                </div>
                <ul className="space-y-6">
                  <li className="flex items-start space-x-4 group">
                    <div className="w-3 h-3 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full mt-1.5 flex-shrink-0 shadow-sm group-hover:scale-125 transition-transform"></div>
                    <span className="text-gray-700 text-base leading-relaxed font-light group-hover:text-gray-900 transition-colors">Technical support and troubleshooting</span>
                  </li>
                  <li className="flex items-start space-x-4 group">
                    <div className="w-3 h-3 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full mt-1.5 flex-shrink-0 shadow-sm group-hover:scale-125 transition-transform"></div>
                    <span className="text-gray-700 text-base leading-relaxed font-light group-hover:text-gray-900 transition-colors">Feature requests and suggestions</span>
                  </li>
                  <li className="flex items-start space-x-4 group">
                    <div className="w-3 h-3 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full mt-1.5 flex-shrink-0 shadow-sm group-hover:scale-125 transition-transform"></div>
                    <span className="text-gray-700 text-base leading-relaxed font-light group-hover:text-gray-900 transition-colors">Partnership and collaboration opportunities</span>
                  </li>
                  <li className="flex items-start space-x-4 group">
                    <div className="w-3 h-3 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full mt-1.5 flex-shrink-0 shadow-sm group-hover:scale-125 transition-transform"></div>
                    <span className="text-gray-700 text-base leading-relaxed font-light group-hover:text-gray-900 transition-colors">General inquiries and feedback</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

