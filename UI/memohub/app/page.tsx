'use client'

import Link from 'next/link'
import { ArrowRight, Menu, X } from 'lucide-react'
import { useState, useEffect } from 'react'

export default function Home() {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  useEffect(() => {
    // Handle URL hash, scroll to about section if hash is #about
    if (window.location.hash === '#about') {
      setTimeout(() => {
        const aboutSection = document.getElementById('about')
        if (aboutSection) {
          aboutSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
        }
      }, 100)
    }
  }, [])

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
                <button
                  onClick={() => {
                    const aboutSection = document.getElementById('about')
                    if (aboutSection) {
                      aboutSection.scrollIntoView({ behavior: 'smooth', block: 'start' })
                    }
                  }}
                  className={`text-gray-800 dark:text-gray-200 nav-link-hover transition-all duration-200 text-left w-full ${
                    sidebarOpen ? 'block' : 'hidden'
                  }`}
                >
                  About
                </button>
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
         <section className="h-[70vh] w-full flex items-center justify-center p-8 gradient-bg">
           <div className="w-full max-w-4xl text-center">
             <p className="text-lg font-light tracking-wider text-white/95 mb-6 uppercase">Private, portable memory for any LLM</p>
             <h1 className="text-5xl lg:text-7xl font-bold text-white mb-10" style={{ textShadow: '0 4px 20px rgba(0, 0, 0, 0.3), 0 2px 10px rgba(0, 0, 0, 0.2)' }}>One Memory, for all you AIs</h1>
             <div className="flex justify-center gap-4">
               <Link href="/login" className="bg-white text-gray-900 font-semibold py-4 px-12 rounded-2xl hover:bg-gray-50 transition-colors duration-200 shadow-lg flex items-center space-x-2 border border-gray-200">
                 <ArrowRight className="w-5 h-5" />
                 <span>Login</span>
               </Link>
               <Link href="/register" className="bg-white/10 backdrop-blur-sm text-white font-semibold py-4 px-12 rounded-2xl hover:bg-white/20 transition-colors duration-200 shadow-lg flex items-center space-x-2 border border-white/20">
                 <ArrowRight className="w-5 h-5" />
                 <span>Register</span>
               </Link>
             </div>
           </div>
         </section>

        {/* Lower part: white background */}
        <section id="about" className="w-full flex-grow p-16 scroll-mt-24">
          <div className="grid grid-cols-2 gap-16 max-w-7xl mx-auto">
            <div>
              <h2 className="text-8xl font-bold tracking-tighter text-black font-display">MemoHub</h2>
            </div>
            <div className="space-y-6 text-gray-600 dark:text-gray-400 pt-2 font-display">
              <p>MemoHub is a personal memory management system designed for the AI era. Through intelligent file processing and natural language retrieval, it empowers your AI assistants with enhanced memory capabilities.</p>
              <p>Supporting multiple file formats including documents, images, and audio, MemoHub leverages advanced vectorization technology to enable cross-modal intelligent search and knowledge management. Whether it's work documents, study notes, or personal collections, MemoHub helps you build a complete knowledge graph, making information easily accessible.</p>
              <p>At its core, MemoHub is about precision and clarity—connecting memories and optimizing AI performance. Our platform provides a unified memory hub that serves all your AI models, enabling seamless knowledge sharing and intelligent retrieval across different applications.</p>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
