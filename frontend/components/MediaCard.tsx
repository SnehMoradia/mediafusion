'use client'

import React from 'react'
import { Play, Music, Film, CheckCircle2, Circle } from 'lucide-react'

export interface Item {
  index: number
  id: string
  title: string
  uploader: string
  duration: number
  thumbnail: string
  url: string
}

export interface MediaData {
  is_playlist: boolean
  title: string
  uploader: string
  thumbnail: string
  total_items: number
  items: Item[]
}

interface MediaCardProps {
  data: MediaData
  selectedIds: string[]
  onToggleSelect: (id: string) => void
  onToggleSelectAll: () => void
}

export default function MediaCard({ data, selectedIds, onToggleSelect, onToggleSelectAll }: MediaCardProps) {
  const isAllSelected = selectedIds.length === data.items.length

  const formatDuration = (sec: number) => {
    if (!sec) return '0:00'
    const m = Math.floor(sec / 60)
    const s = Math.floor(sec % 60)
    return `${m}:${s < 10 ? '0' : ''}${s}`
  }

  return (
    <div className="glass-panel rounded-2xl p-6 mb-6">
      <div className="flex flex-col md:flex-row gap-6 items-start border-b border-gray-800 pb-6 mb-6">
        {data.thumbnail && (
          <img 
            src={data.thumbnail} 
            alt={data.title} 
            className="w-full md:w-48 h-32 object-cover rounded-xl shadow-lg border border-gray-800"
          />
        )}
        <div className="flex-1">
          <span className="inline-block px-3 py-1 bg-indigo-500/20 text-indigo-400 text-xs font-semibold rounded-full mb-2">
            {data.is_playlist ? 'Playlist' : 'Single Item'} • {data.total_items} item(s)
          </span>
          <h2 className="text-2xl font-bold text-white mb-1 line-clamp-2">{data.title}</h2>
          <p className="text-gray-400 text-sm">{data.uploader}</p>
        </div>
      </div>

      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
          Items ({selectedIds.length}/{data.items.length} selected)
        </h3>
        <button
          onClick={onToggleSelectAll}
          className="text-xs text-indigo-400 hover:text-indigo-300 font-medium transition"
        >
          {isAllSelected ? 'Deselect All' : 'Select All'}
        </button>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto pr-2 custom-scrollbar">
        {data.items.map((item) => {
          const isSelected = selectedIds.includes(item.id)
          return (
            <div
              key={item.id}
              onClick={() => onToggleSelect(item.id)}
              className={`flex items-center space-x-4 p-3 rounded-xl cursor-pointer border transition ${
                isSelected 
                  ? 'bg-indigo-600/10 border-indigo-500/50 text-white' 
                  : 'bg-gray-900/40 border-gray-800 text-gray-400 hover:border-gray-700'
              }`}
            >
              <div className="text-indigo-400">
                {isSelected ? <CheckCircle2 className="w-5 h-5" /> : <Circle className="w-5 h-5 text-gray-600" />}
              </div>
              <img 
                src={item.thumbnail} 
                alt={item.title} 
                className="w-12 h-12 object-cover rounded-lg bg-gray-800"
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-200 truncate">{item.title}</p>
                <p className="text-xs text-gray-500">{item.uploader} • {formatDuration(item.duration)}</p>
              </div>
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                onClick={(e) => e.stopPropagation()}
                className="px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-400 text-xs font-semibold rounded-lg border border-indigo-500/30 transition flex items-center space-x-1"
              >
                <span>Watch / Source</span>
              </a>
            </div>
          )
        })}
      </div>
    </div>
  )
}
