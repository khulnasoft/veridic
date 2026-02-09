'use client'

export function CTA() {
  return (
    <section className="py-24 px-6 border-t border-border">
      <div className="max-w-4xl mx-auto text-center space-y-8">
        <h2 className="text-4xl md:text-5xl font-bold text-foreground text-balance">
          Ready to build faster?
        </h2>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Join thousands of teams who trust Veridic to deploy their most critical applications.
        </p>
        <div className="flex flex-col md:flex-row items-center justify-center gap-4 pt-4">
          <button className="bg-primary text-primary-foreground px-8 py-3 rounded-full font-medium hover:bg-primary/90 smooth-transition w-full md:w-auto">
            Start Building
          </button>
          <button className="border border-border text-foreground px-8 py-3 rounded-full font-medium hover:bg-accent/30 smooth-transition w-full md:w-auto">
            View Documentation
          </button>
        </div>
      </div>
    </section>
  )
}
