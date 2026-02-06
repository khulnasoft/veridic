'use client'

import Link from 'next/link'
import { Github, Twitter, Linkedin } from 'lucide-react'

export function Footer() {
  const sections = {
    Product: ['Features', 'Pricing', 'Enterprise', 'Templates'],
    Company: ['About', 'Blog', 'Careers', 'Contact'],
    Resources: ['Docs', 'Guides', 'API', 'Community'],
    Legal: ['Privacy', 'Terms', 'Security', 'Status'],
  }

  return (
    <footer className="border-t border-border py-16 px-6 bg-secondary/30">
      <div className="max-w-6xl mx-auto">
        {/* Main Footer */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-12 mb-12">
          {/* Brand */}
          <div className="space-y-4">
            <Link href="/" className="flex items-center gap-2 text-lg font-bold">
              <div className="w-6 h-6 bg-primary rounded-sm flex items-center justify-center">
                <span className="text-primary-foreground text-xs font-black">V</span>
              </div>
              <span>Veridic</span>
            </Link>
            <p className="text-muted-foreground text-sm">
              The complete platform to build the web.
            </p>
            <div className="flex gap-4 pt-2">
              <a href="#" className="text-muted-foreground hover:text-foreground smooth-transition">
                <Github size={20} />
              </a>
              <a href="#" className="text-muted-foreground hover:text-foreground smooth-transition">
                <Twitter size={20} />
              </a>
              <a href="#" className="text-muted-foreground hover:text-foreground smooth-transition">
                <Linkedin size={20} />
              </a>
            </div>
          </div>

          {/* Links Sections */}
          {Object.entries(sections).map(([title, links]) => (
            <div key={title}>
              <h4 className="font-semibold text-foreground mb-4 text-sm uppercase tracking-wide">
                {title}
              </h4>
              <ul className="space-y-3">
                {links.map((link) => (
                  <li key={link}>
                    <Link
                      href="#"
                      className="text-sm text-muted-foreground hover:text-foreground smooth-transition"
                    >
                      {link}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Section */}
        <div className="border-t border-border pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-muted-foreground">
            © 2024 Veridic. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            <button className="text-sm text-muted-foreground hover:text-foreground smooth-transition">
              Status
            </button>
            <button className="text-sm text-muted-foreground hover:text-foreground smooth-transition">
              System Status
            </button>
          </div>
        </div>
      </div>
    </footer>
  )
}
