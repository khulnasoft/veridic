'use client'

import { ReactNode } from 'react'

interface FeatureCardProps {
  icon: ReactNode
  title: string
  description: string
  cta?: string
}

export function FeatureCard({ icon, title, description, cta }: FeatureCardProps) {
  return (
    <div className="group border border-border rounded-lg p-8 hover:border-primary/50 hover:bg-accent/20 smooth-transition cursor-pointer h-full flex flex-col">
      <div className="text-primary mb-4 group-hover:scale-110 smooth-transition inline-block">
        {icon}
      </div>
      <h3 className="text-xl font-semibold text-foreground mb-3">{title}</h3>
      <p className="text-muted-foreground flex-grow mb-6">{description}</p>
      {cta && (
        <div className="inline-flex items-center text-primary font-medium text-sm group-hover:gap-2 gap-1 smooth-transition">
          {cta}
          <span>→</span>
        </div>
      )}
    </div>
  )
}
