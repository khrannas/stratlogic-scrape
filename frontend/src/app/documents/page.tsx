'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Filter, Download, Eye } from 'lucide-react'
import api from '@/lib/api'
import { Artifact, DocumentFilters } from '@/types'
import { Header } from '@/components/header'
import { Sidebar } from '@/components/sidebar'
import { useAuth } from '@/hooks/use-auth'

export default function DocumentsPage() {
    const { user, isAuthenticated } = useAuth()
    const [filters, setFilters] = useState<DocumentFilters>({
        search: '',
        source_type: undefined,
        page: 1,
        size: 20,
    })

    const { data: documents, isLoading } = useQuery({
        queryKey: ['documents', filters],
        queryFn: async () => {
            const params = new URLSearchParams()
            if (filters.search) params.append('search', filters.search)
            if (filters.source_type) params.append('source_type', filters.source_type)
            if (filters.page) params.append('page', filters.page.toString())
            if (filters.size) params.append('size', filters.size.toString())

            const response = await api.get(`/api/artifacts?${params.toString()}`)
            return response.data
        },
        enabled: isAuthenticated,
    })

    const handleSearch = (search: string) => {
        setFilters(prev => ({ ...prev, search, page: 1 }))
    }

    const handleSourceTypeChange = (sourceType: string) => {
        setFilters(prev => ({
            ...prev,
            source_type: sourceType === 'all' ? undefined : sourceType as any,
            page: 1
        }))
    }

    if (!isAuthenticated) {
        return (
            <div className="flex h-screen items-center justify-center">
                <p>Please log in to view documents</p>
            </div>
        )
    }

    return (
        <div className="flex h-screen bg-gray-50">
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
                <Header user={user} />
                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50">
                    <div className="container mx-auto px-6 py-8">
                        <div className="space-y-6">
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
                                <p className="text-gray-600">Browse and search scraped documents</p>
                            </div>

                            {/* Search and Filters */}
                            <div className="bg-white rounded-lg shadow p-6">
                                <div className="flex flex-col md:flex-row gap-4">
                                    <div className="flex-1">
                                        <div className="relative">
                                            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                                            <input
                                                type="text"
                                                placeholder="Search documents..."
                                                value={filters.search || ''}
                                                onChange={(e) => handleSearch(e.target.value)}
                                                className="input pl-10"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex items-center space-x-4">
                                        <select
                                            value={filters.source_type || 'all'}
                                            onChange={(e) => handleSourceTypeChange(e.target.value)}
                                            className="input"
                                        >
                                            <option value="all">All Sources</option>
                                            <option value="web">Web</option>
                                            <option value="paper">Paper</option>
                                            <option value="government">Government</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* Documents List */}
                            <div className="bg-white rounded-lg shadow">
                                {isLoading ? (
                                    <div className="p-8 text-center">
                                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
                                        <p className="mt-2 text-gray-600">Loading documents...</p>
                                    </div>
                                ) : (
                                    <div className="divide-y divide-gray-200">
                                        {documents?.data?.map((doc: Artifact) => (
                                            <div key={doc.id} className="p-6">
                                                <div className="flex items-start justify-between">
                                                    <div className="flex-1">
                                                        <h3 className="text-lg font-medium text-gray-900 mb-2">
                                                            {doc.title}
                                                        </h3>
                                                        <p className="text-gray-600 text-sm mb-2 line-clamp-3">
                                                            {doc.content.substring(0, 200)}...
                                                        </p>
                                                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                                                            <span className="capitalize">{doc.source_type}</span>
                                                            <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                                                            {doc.url && (
                                                                <a
                                                                    href={doc.url}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="text-primary-600 hover:text-primary-700"
                                                                >
                                                                    View Source
                                                                </a>
                                                            )}
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center space-x-2 ml-4">
                                                        <button className="p-2 text-gray-400 hover:text-gray-600">
                                                            <Eye className="w-5 h-5" />
                                                        </button>
                                                        <button className="p-2 text-gray-400 hover:text-gray-600">
                                                            <Download className="w-5 h-5" />
                                                        </button>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                        {(!documents?.data || documents.data.length === 0) && (
                                            <div className="p-8 text-center">
                                                <p className="text-gray-500">No documents found</p>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    )
}
