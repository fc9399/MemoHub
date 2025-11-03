import { ReactNode } from 'react'

interface GradientBGProps {
  children: ReactNode
  className?: string
}

export function GradientBG({ children, className = '' }: GradientBGProps) {
  return (
    <div className={`bg-radial-brand bg-noise-overlay min-h-screen ${className}`}>
      {children}
    </div>
  )
}



