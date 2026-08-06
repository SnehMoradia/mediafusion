'use client'

import React, { useState } from 'react'
import { Link2, Cookie, Download, Loader2, Sparkles, AlertCircle } from 'lucide-react'
import MediaCard, { MediaData } from '../components/MediaCard'
import CookieModal from '../components/CookieModal'

export default function Home() {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mediaData, setMediaData] = useState<MediaData | null>(null)
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  
  // Custom cookies state
  const [cookies, setCookies] = useState<string>('')
  const [isCookieModalOpen, setIsCookieModalOpen] = useState(false)

  // Options
  const [format, setFormat] = useState('video')
  const [quality, setQuality] = useState('best')

  const handleExtract = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return

    setLoading(true)
    setError(null)
    setMediaData(null)

    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || '/api'
      const res = await fetch(`${apiHost}/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim(), cookies })
      })

      const json = await res.json()
      if (json.success) {
        setMediaData(json.data)
        setSelectedIds(json.data.items.map((i: any) => i.id))
      } else {
        setError(json.error || 'Failed to fetch media details.')
      }
    } catch (err: any) {
      setError(err.message || 'An error occurred while connecting to backend server.')
    } finally {
      setLoading(false)
    }
  }

  const toggleSelect = (id: string) => {
    if (selectedIds.includes(id)) {
      setSelectedIds(selectedIds.filter(i => i !== id))
    } else {
      setSelectedIds([...selectedIds, id])
    }
  }

  const toggleSelectAll = () => {
    if (!mediaData) return
    if (selectedIds.length === mediaData.items.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(mediaData.items.map(i => i.id))
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-3 bg-gradient-to-tr from-indigo-600 to-purple-600 rounded-2xl shadow-lg shadow-indigo-600/30">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-white">MediaFusion</h1>
            <p className="text-xs text-gray-400 font-medium">Universal Playlist & Media Downloader</p>
          </div>
        </div>

        <button
          onClick={() => setIsCookieModalOpen(true)}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold border transition ${
            cookies.trim() 
              ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-400' 
              : 'bg-gray-800/60 border-gray-700/60 text-gray-300 hover:border-gray-600'
          }`}
        >
          <Cookie className="w-4 h-4" />
          <span>{cookies.trim() ? 'Cookies Active' : 'Custom Cookies'}</span>
        </button>
      </header>

      {/* Main Search Input Form */}
      <div className="glass-panel rounded-3xl p-6 shadow-2xl">
        <form onSubmit={handleExtract} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Link2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste YouTube, Spotify, or Instagram link..."
              className="w-full bg-gray-900/90 text-white placeholder-gray-500 text-sm pl-12 pr-4 py-3.5 rounded-2xl border border-gray-700/60 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 transition"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="flex items-center justify-center space-x-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-sm px-6 py-3.5 rounded-2xl shadow-lg shadow-indigo-600/30 transition disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <span>Fetch Media</span>}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-500/10 border border-red-500/30 rounded-2xl flex items-start space-x-3 text-red-400 text-xs">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <p className="leading-relaxed">{error}</p>
          </div>
        )}
      </div>

      {/* Media Details Component */}
      {mediaData && (
        <MediaCard
          data={mediaData}
          selectedIds={selectedIds}
          onToggleSelect={toggleSelect}
          onToggleSelectAll={toggleSelectAll}
        />
      )}

      {/* Cookie Setup Modal */}
      <CookieModal
        isOpen={isCookieModalOpen}
        onClose={() => setIsCookieModalOpen(false)}
        onSaveCookies={(c) => setCookies(c)}
        currentCookies={cookies}
      />
    </div>
  )
}
