'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Menu, X } from 'lucide-react'

export function Header() {
  const [isOpen, setIsOpen] = useState(false)

  const navItems = [
    { label: 'Showcase', href: '#showcase' },
    { label: 'Docs', href: '#docs' },
    { label: 'Blog', href: '#blog' },
    { label: 'Templates', href: '#templates' },
    { label: 'Enterprise', href: '#enterprise' },
  ]

  return (
    <header className="fixed top-0 w-full bg-background/80 backdrop-blur-md border-b border-border z-50">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 text-2xl font-bold">
            <div className="w-6 h-6 bg-primary rounded-sm flex items-center justify-center">
              <span className="text-primary-foreground text-sm font-black">V</span>
            </div>
            <span className="text-foreground">Veridic</span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            {navItems.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="text-muted-foreground hover:text-foreground smooth-transition text-sm"
              >
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-4">
            <button className="hidden md:inline-flex text-sm text-muted-foreground hover:text-foreground smooth-transition">
              Sign In
            </button>
            <button className="bg-primary text-primary-foreground px-6 py-2 rounded-full text-sm font-medium hover:bg-primary/90 smooth-transition">
              Get Started
            </button>

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="md:hidden text-foreground"
              aria-label="Toggle menu"
            >
              {isOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isOpen && (
          <nav className="md:hidden mt-4 pb-4 flex flex-col gap-4 border-t border-border pt-4">
            {navItems.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="text-muted-foreground hover:text-foreground smooth-transition text-sm"
                onClick={() => setIsOpen(false)}
              >
                {item.label}
              </Link>
            ))}
            <button className="text-left text-sm text-muted-foreground hover:text-foreground smooth-transition">
              Sign In
            </button>
          </nav>
        )}
      </div>
    </header>
  )
}
