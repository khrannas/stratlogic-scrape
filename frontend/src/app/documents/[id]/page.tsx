'use client'

import { useParams } from 'next/navigation'
import { useDocument } from '@/hooks/use-documents'
import { formatDateTime } from '@/lib/utils'
import { Globe, FileText, Building, ExternalLink, ArrowLeft } from 'lucide-react'
import Link from 'next/link'

export default function DocumentDetailPage() {
  const params = useParams()
  const documentId = params.id as string
  
  const { data: document, isLoading, error } = useDocument(documentId)

  const getSourceIcon = (sourceType: string) => {
    switch (sourceType) {
      case 'web':
        return <Globe className="h-5 w-5 text-blue-600" />
      case 'paper':
        return <FileText className="h-5 w-5 text-green-600" />
      case 'government':
        return <Building className="h-5 w-5 text-purple-600" />
      default:
        return <FileText className="h-5 w-5 text-gray-600" />
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

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex justify-center items-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading document...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !document) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-6">
          <p className="text-red-600">Error loading document: {error?.message || 'Document not found'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/documents" className="text-blue-600 hover:text-blue-800 mb-4 inline-flex items-center">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Documents
          </Link>
          
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {document.title}
              </h1>
              <div className="flex items-center space-x-3">
                {getSourceIcon(document.source_type)}
                <span className={`px-2 py-1 rounded-full text-sm font-medium ${getSourceColor(document.source_type)}`}>
                  {document.source_type}
                </span>
                {document.source_url && (
                  <a
                    href={document.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Document Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-medium text-gray-900">Content</h2>
              </div>
              <div className="p-6">
                <div className="prose max-w-none">
                  <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                    {document.content}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Metadata Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">Document Information</h3>
              </div>
              <div className="p-6">
                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Document ID</h4>
                    <p className="text-sm text-gray-900 font-mono">{document.id}</p>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Source Type</h4>
                    <div className="flex items-center space-x-2">
                      {getSourceIcon(document.source_type)}
                      <span className="text-sm text-gray-900 capitalize">{document.source_type}</span>
                    </div>
                  </div>

                  {document.source_url && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-1">Source URL</h4>
                      <a
                        href={document.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:text-blue-800 break-all"
                      >
                        {document.source_url}
                      </a>
                    </div>
                  )}

                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Created</h4>
                    <p className="text-sm text-gray-900">{formatDateTime(document.created_at)}</p>
                  </div>

                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Updated</h4>
                    <p className="text-sm text-gray-900">{formatDateTime(document.updated_at)}</p>
                  </div>

                  {document.metadata && Object.keys(document.metadata).length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Metadata</h4>
                      <div className="space-y-2">
                        {Object.entries(document.metadata).map(([key, value]) => (
                          <div key={key} className="text-sm">
                            <span className="font-medium text-gray-700">{key}:</span>
                            <span className="text-gray-900 ml-1">
                              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
