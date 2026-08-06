'use client'

import React, { useState } from 'react'
import { Cookie, X, Check } from 'lucide-react'

interface CookieModalProps {
  isOpen: boolean
  onClose: () => void
  onSaveCookies: (cookieStr: string) => void
  currentCookies: string
}

export default function CookieModal({ isOpen, onClose, onSaveCookies, currentCookies }: CookieModalProps) {
  const [cookies, setCookies] = useState(currentCookies)

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="glass-panel w-full max-w-xl rounded-2xl p-6 relative animate-in fade-in zoom-in-95">
        <button 
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white p-1 rounded-lg transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2.5 bg-indigo-500/20 text-indigo-400 rounded-xl">
            <Cookie className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-white">Custom Cookies Setup</h3>
            <p className="text-sm text-gray-400">Bypass YouTube sign-in bot checks using your own session cookies</p>
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-xs font-semibold uppercase text-gray-400 tracking-wider mb-2">
            Netscape / Netscape HTTP Cookie Format (cookies.txt content)
          </label>
          <textarea
            value={cookies}
            onChange={(e) => setCookies(e.target.value)}
            placeholder="# Netscape HTTP Cookie File&#10;.youtube.com TRUE / TRUE 0 VISITOR_INFO1_LIVE xxx..."
            rows={8}
            className="w-full bg-gray-900/80 text-gray-200 text-xs font-mono p-3 rounded-xl border border-gray-700/50 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        <div className="flex justify-end space-x-3">
          <button
            onClick={() => { setCookies(''); onSaveCookies(''); onClose(); }}
            className="px-4 py-2 text-sm text-gray-400 hover:text-white transition"
          >
            Clear Cookies
          </button>
          <button
            onClick={() => { onSaveCookies(cookies); onClose(); }}
            className="flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-5 py-2 rounded-xl transition shadow-lg shadow-indigo-600/30"
          >
            <Check className="w-4 h-4" />
            <span>Save Cookies</span>
          </button>
        </div>
      </div>
    </div>
  )
}
