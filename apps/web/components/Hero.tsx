'use client'

import { ArrowRight } from 'lucide-react'

export function Hero() {
  return (
    <section className="min-h-screen pt-32 pb-20 px-6 flex items-center justify-center">
      <div className="max-w-6xl mx-auto text-center space-y-8">
        {/* Main Heading */}
        <div className="space-y-4">
          <h1 className="text-5xl md:text-7xl font-bold text-balance leading-tight">
            The complete platform
            <br />
            to build the web.
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto text-balance">
            Your team's toolkit to stop configuring and start innovating. Securely build, deploy, and scale the best web experiences with Veridic.
          </p>
        </div>

        {/* CTAs */}
        <div className="flex flex-col md:flex-row items-center justify-center gap-4">
          <button className="bg-primary text-primary-foreground px-8 py-3 rounded-full font-medium hover:bg-primary/90 smooth-transition flex items-center gap-2 w-full md:w-auto justify-center">
            Get a demo
            <ArrowRight size={18} />
          </button>
          <button className="border border-border text-foreground px-8 py-3 rounded-full font-medium hover:bg-accent/30 smooth-transition w-full md:w-auto">
            Explore the Product
          </button>
        </div>

        {/* Stats Grid */}
        <div className="pt-12 grid grid-cols-1 md:grid-cols-4 gap-4 border-t border-border mt-16">
          <div className="py-6 px-4">
            <div className="text-3xl md:text-4xl font-bold text-primary mb-2">20 days</div>
            <p className="text-sm text-muted-foreground">saved on daily builds.</p>
          </div>
          <div className="py-6 px-4">
            <div className="text-3xl md:text-4xl font-bold text-primary mb-2">98%</div>
            <p className="text-sm text-muted-foreground">faster time to market.</p>
          </div>
          <div className="py-6 px-4">
            <div className="text-3xl md:text-4xl font-bold text-primary mb-2">300%</div>
            <p className="text-sm text-muted-foreground">increase in SEO.</p>
          </div>
          <div className="py-6 px-4">
            <div className="text-3xl md:text-4xl font-bold text-primary mb-2">6x</div>
            <p className="text-sm text-muted-foreground">faster to build + deploy.</p>
          </div>
        </div>

        {/* Companies */}
        <div className="pt-12 border-t border-border">
          <p className="text-xs text-muted-foreground mb-8 uppercase tracking-wide">Trusted by global teams</p>
          <div className="flex flex-wrap items-center justify-center gap-8 md:gap-12">
            {['Netflix', 'TripAdvisor', 'Box', 'eBay'].map((company) => (
              <div key={company} className="text-lg font-semibold text-muted-foreground opacity-60 hover:opacity-100 smooth-transition">
                {company}
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
