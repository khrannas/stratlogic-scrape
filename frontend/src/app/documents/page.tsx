'use client'

import { useState } from 'react'
import { useDocuments } from '@/hooks/use-documents'
import { DocumentCard } from '@/components/documents/document-card'
import { DocumentFilters } from '@/components/documents/document-filters'
import { FileText, Search } from 'lucide-react'

export default function DocumentsPage() {
  const [search, setSearch] = useState('')
  const [sourceType, setSourceType] = useState('')
  const [page, setPage] = useState(1)
  
  const { data: documentsData, isLoading, error } = useDocuments(page, 20, search)

  const filteredDocuments = documentsData?.items.filter(doc => 
    !sourceType || doc.source_type === sourceType
  ) || []

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Documents
          </h1>
          <p className="text-gray-600">
            Browse and search through all collected documents from various sources.
          </p>
        </div>

        {/* Stats */}
        {documentsData && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <FileText className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Documents</p>
                  <p className="text-2xl font-bold text-gray-900">{documentsData.total}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filters */}
        <DocumentFilters
          search={search}
          onSearchChange={setSearch}
          sourceType={sourceType}
          onSourceTypeChange={setSourceType}
        />

        {/* Documents List */}
        {isLoading ? (
          <div className="flex justify-center items-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading documents...</p>
            </div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-md p-6">
            <p className="text-red-600">Error loading documents: {error.message}</p>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <Search className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No documents found</h3>
            <p className="text-gray-600">
              {search || sourceType 
                ? 'Try adjusting your search or filters.' 
                : 'No documents have been collected yet. Start a scraping job to collect documents.'
              }
            </p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {filteredDocuments.map((document) => (
                <DocumentCard key={document.id} document={document} />
              ))}
            </div>

            {/* Pagination */}
            {documentsData && documentsData.pages > 1 && (
              <div className="flex justify-center">
                <nav className="flex items-center space-x-2">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  
                  <span className="px-3 py-2 text-sm text-gray-700">
                    Page {page} of {documentsData.pages}
                  </span>
                  
                  <button
                    onClick={() => setPage(Math.min(documentsData.pages, page + 1))}
                    disabled={page === documentsData.pages}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </nav>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
