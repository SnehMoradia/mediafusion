import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'MediaFusion - Modern Media Downloader',
  description: 'Download YouTube playlists, Spotify tracks, and Instagram reels effortlessly.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        <main className="container mx-auto px-4 py-8 max-w-5xl">
          {children}
        </main>
      </body>
    </html>
  )
}
