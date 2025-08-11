'use client'

import { useState } from 'react'
import { Search, Filter, X } from 'lucide-react'

interface DocumentFiltersProps {
  search: string
  onSearchChange: (search: string) => void
  sourceType: string
  onSourceTypeChange: (type: string) => void
}

export function DocumentFilters({ 
  search, 
  onSearchChange, 
  sourceType, 
  onSourceTypeChange 
}: DocumentFiltersProps) {
  const [showFilters, setShowFilters] = useState(false)

  const sourceTypes = [
    { value: '', label: 'All Sources' },
    { value: 'web', label: 'Web' },
    { value: 'paper', label: 'Paper' },
    { value: 'government', label: 'Government' },
  ]

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      {/* Search Bar */}
      <div className="flex items-center space-x-4 mb-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search documents..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {search && (
            <button
              onClick={() => onSearchChange('')}
              className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center space-x-2 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
        >
          <Filter className="h-4 w-4" />
          <span>Filters</span>
        </button>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="border-t border-gray-200 pt-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Source Type
              </label>
              <select
                value={sourceType}
                onChange={(e) => onSourceTypeChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {sourceTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
