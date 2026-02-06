'use client'

import { Zap, Gauge, Lock, Globe } from 'lucide-react'
import { FeatureCard } from './FeatureCard'

export function Features() {
  const features = [
    {
      icon: <Zap size={32} />,
      title: 'Lightning Fast',
      description: 'Deploy globally with automatic performance optimization and edge computing.',
      cta: 'Learn more',
    },
    {
      icon: <Gauge size={32} />,
      title: 'Developer Experience',
      description: 'Intuitive tools and seamless workflows designed for modern development.',
      cta: 'Explore',
    },
    {
      icon: <Lock size={32} />,
      title: 'Enterprise Security',
      description: 'Bank-level security with advanced compliance and data protection.',
      cta: 'View features',
    },
    {
      icon: <Globe size={32} />,
      title: 'Global Scale',
      description: 'Deliver content at scale with our worldwide edge network.',
      cta: 'Discover',
    },
  ]

  return (
    <section className="py-24 px-6 border-t border-border">
      <div className="max-w-6xl mx-auto">
        <div className="space-y-4 mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-foreground">
            Everything you need to succeed
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl">
            A comprehensive platform with all the tools developers need to build, deploy, and scale modern web applications.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <FeatureCard key={index} {...feature} />
          ))}
        </div>
      </div>
    </section>
  )
}
