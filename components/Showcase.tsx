'use client'

export function Showcase() {
  return (
    <section className="py-24 px-6 border-t border-border">
      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
        {/* Left Column - Content */}
        <div className="space-y-6">
          <div className="inline-flex items-center gap-2 text-sm text-primary">
            <span className="text-xl">✨</span>
            <span>Collaboration</span>
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-foreground">
            Make teamwork seamless.
          </h2>
          <p className="text-lg text-muted-foreground leading-relaxed">
            Tools for your team and stakeholders to share feedback and iterate faster. Enable real-time collaboration, centralized reviews, and streamlined deployment workflows for teams of all sizes.
          </p>
          <div className="pt-4">
            <button className="inline-flex items-center text-primary font-medium hover:gap-2 gap-1 smooth-transition">
              Learn about collaboration
              <span>→</span>
            </button>
          </div>
        </div>

        {/* Right Column - Visual */}
        <div className="relative">
          <div className="bg-accent/30 border border-border rounded-lg p-8 space-y-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="w-2 h-2 bg-primary rounded-full"></div>
                <span>monitoring-query-variant</span>
              </div>
              <div className="flex items-center gap-2 text-sm">
                <div className="w-4 h-4 border border-border rounded"></div>
                <span className="text-foreground font-mono">Query ("queryEngine")</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>Select an override...</span>
              </div>
            </div>
            <div className="h-40 bg-secondary/20 rounded border border-border flex items-center justify-center">
              <span className="text-muted-foreground text-sm">Interactive Demo</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
