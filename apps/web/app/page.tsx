import { Header } from '@/components/Header'
import { Hero } from '@/components/Hero'
import { Features } from '@/components/Features'
import { Showcase } from '@/components/Showcase'
import { CTA } from '@/components/CTA'
import { Footer } from '@/components/Footer'

export default function Page() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <Header />
      <Hero />
      <Features />
      <Showcase />
      <CTA />
      <Footer />
    </main>
  )
}
