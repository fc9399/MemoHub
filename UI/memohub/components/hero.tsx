import Link from 'next/link'
import { ArrowRight } from 'lucide-react'

export function Hero() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative">
      {/* MemoHub Title - Semi-transparent background title */}
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-0">
        <h1 className="text-8xl md:text-9xl font-extrabold text-white/10 select-none font-display">
          MemoHub
        </h1>
      </div>
      
      {/* Main content area */}
      <div className="relative z-10 text-center">
        {/* Eyebrow */}
        <p className="text-sm text-white/80 mb-4 font-medium font-display">
          Private, portable memory for any LLM
        </p>
        
        {/* Main Heading */}
        <h2 className="text-5xl lg:text-7xl font-extrabold text-white mb-10 leading-tight font-display">
          One Memory, for all your AIs
        </h2>
        
        {/* Slowly appearing login/register box */}
        <div className="animate-fade-in-up">
          <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-8 shadow-brand border border-white/20">
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link
                href="/login"
                className="bg-white text-gray-900 px-8 py-4 rounded-2xl font-semibold text-lg hover:bg-gray-100 transition-colors shadow-brand flex items-center space-x-2"
              >
                <ArrowRight className="w-5 h-5" />
                <span>Login</span>
              </Link>
              <Link
                href="/register"
                className="bg-white/20 text-white px-8 py-4 rounded-2xl font-semibold text-lg hover:bg-white/30 transition-colors border border-white/30 flex items-center space-x-2"
              >
                <ArrowRight className="w-5 h-5" />
                <span>Register</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}