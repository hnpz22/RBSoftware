import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'
import './globals.css'
import { Providers } from '@/components/providers'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'RBSoftware · ROBOTSchool',
  description: 'Plataforma de gestión operativa y académica de ROBOTSchool',
  icons: {
    icon: '/favicon.svg',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={inter.variable}>
      <body>
        <Providers>{children}</Providers>
        <Script
          src="https://acrobatservices.adobe.com/view-sdk/viewer.js"
          strategy="beforeInteractive"
        />
      </body>
    </html>
  )
}
