'use client'

import { Document } from '@/types'
import { formatDate, truncateText } from '@/lib/utils'
import { FileText, Globe, Building, ExternalLink } from 'lucide-react'
import Link from 'next/link'

interface DocumentCardProps {
  document: Document
}

export function DocumentCard({ document }: DocumentCardProps) {
  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'web':
        return <Globe className="h-4 w-4 text-blue-600" />
      case 'paper':
        return <FileText className="h-4 w-4 text-green-600" />
      case 'government':
        return <Building className="h-4 w-4 text-purple-600" />
      default:
        return <FileText className="h-4 w-4 text-gray-600" />
    }
  }

  const getSourceColor = (sourceType: string) => {
    switch (sourceType) {
      case 'web':
        return 'bg-blue-100 text-blue-800'
      case 'paper':
        return 'bg-green-100 text-green-800'
      case 'government':
        return 'bg-purple-100 text-purple-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-2">
            {getSourceIcon(document.source_type)}
            <span className={`text-xs font-medium px-2 py-1 rounded-full ${getSourceColor(document.source_type)}`}>
              {document.source_type}
            </span>
          </div>
          {document.source_url && (
            <a
              href={document.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          )}
        </div>

        <Link href={`/documents/${document.id}`}>
          <h3 className="text-lg font-medium text-gray-900 mb-2 hover:text-blue-600 transition-colors">
            {document.title}
          </h3>
        </Link>

        <p className="text-gray-600 text-sm mb-4 line-clamp-3">
          {truncateText(document.content, 200)}
        </p>

        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Created: {formatDate(document.created_at)}</span>
          <span>Updated: {formatDate(document.updated_at)}</span>
        </div>

        {document.metadata && Object.keys(document.metadata).length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex flex-wrap gap-2">
              {Object.entries(document.metadata).slice(0, 3).map(([key, value]) => (
                <span
                  key={key}
                  className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
                  title={`${key}: ${value}`}
                >
                  {key}: {String(value).length > 20 ? truncateText(String(value), 20) : value}
                </span>
              ))}
              {Object.keys(document.metadata).length > 3 && (
                <span className="text-xs text-gray-500">
                  +{Object.keys(document.metadata).length - 3} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
