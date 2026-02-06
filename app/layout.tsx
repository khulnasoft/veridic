import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'

import './globals.css'

const _geist = Geist({ subsets: ['latin'] })
const _geistMono = Geist_Mono({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Veridic - The complete platform to build the web',
  description: 'Build, deploy, and scale the best web experiences with Veridic. Your team\'s toolkit to stop configuring and start innovating.',
  generator: 'v0.app',
  openGraph: {
    title: 'Veridic - The complete platform to build the web',
    description: 'Build, deploy, and scale web applications with a comprehensive developer platform.',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  )
}
