'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { Search, Globe, FileText, Building } from 'lucide-react'
import api from '@/lib/api'
import { CreateJobRequest } from '@/types'
import { Header } from '@/components/header'
import { Sidebar } from '@/components/sidebar'
import { useAuth } from '@/hooks/use-auth'
import toast from 'react-hot-toast'

export default function ScrapingPage() {
    const { user, isAuthenticated } = useAuth()
    const router = useRouter()
    const queryClient = useQueryClient()

    const [formData, setFormData] = useState({
        job_type: 'web_scraper' as const,
        keywords: '',
        max_results: 10,
    })

    const createJobMutation = useMutation({
        mutationFn: async (data: CreateJobRequest) => {
            const response = await api.post('/api/v1/jobs/', data)
            return response.data
        },
        onSuccess: (data) => {
            toast.success('Scraping job created successfully!')
            queryClient.invalidateQueries({ queryKey: ['jobs'] })
            router.push(`/jobs/${data.id}`)
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to create job')
        },
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        const keywords = formData.keywords.split(',').map(k => k.trim()).filter(k => k)

        if (keywords.length === 0) {
            toast.error('Please enter at least one keyword')
            return
        }

        createJobMutation.mutate({
            job_type: formData.job_type,
            keywords,
            max_results: formData.max_results,
        })
    }

    const scraperTypes = [
        {
            id: 'web_scraper',
            name: 'Web Scraper',
            description: 'Search and scrape web content',
            icon: Globe,
        },
        {
            id: 'paper_scraper',
            name: 'Paper Scraper',
            description: 'Search academic papers and research',
            icon: FileText,
        },
        {
            id: 'government_scraper',
            name: 'Government Scraper',
            description: 'Search government documents and reports',
            icon: Building,
        },
    ]

    if (!isAuthenticated) {
        return (
            <div className="flex h-screen items-center justify-center">
                <p>Please log in to create scraping jobs</p>
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
                        <div className="max-w-2xl mx-auto space-y-6">
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">Create Scraping Job</h1>
                                <p className="text-gray-600">Start a new scraping job to collect documents</p>
                            </div>

                            <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
                                {/* Scraper Type Selection */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-3">
                                        Scraper Type
                                    </label>
                                    <div className="grid grid-cols-1 gap-3">
                                        {scraperTypes.map((type) => {
                                            const Icon = type.icon
                                            return (
                                                <label
                                                    key={type.id}
                                                    className={`relative flex cursor-pointer rounded-lg border p-4 shadow-sm focus:outline-none ${formData.job_type === type.id
                                                        ? 'border-primary-500 ring-2 ring-primary-500'
                                                        : 'border-gray-300'
                                                        }`}
                                                >
                                                    <input
                                                        type="radio"
                                                        name="scraper_type"
                                                        value={type.id}
                                                        checked={formData.job_type === type.id}
                                                        onChange={(e) => setFormData(prev => ({ ...prev, job_type: e.target.value as any }))}
                                                        className="sr-only"
                                                    />
                                                    <div className="flex items-center">
                                                        <div className="flex-shrink-0">
                                                            <Icon className="h-6 w-6 text-gray-400" />
                                                        </div>
                                                        <div className="ml-3">
                                                            <p className="text-sm font-medium text-gray-900">{type.name}</p>
                                                            <p className="text-sm text-gray-500">{type.description}</p>
                                                        </div>
                                                    </div>
                                                </label>
                                            )
                                        })}
                                    </div>
                                </div>

                                {/* Keywords */}
                                <div>
                                    <label htmlFor="keywords" className="block text-sm font-medium text-gray-700 mb-2">
                                        Keywords (comma-separated)
                                    </label>
                                    <textarea
                                        id="keywords"
                                        value={formData.keywords}
                                        onChange={(e) => setFormData(prev => ({ ...prev, keywords: e.target.value }))}
                                        placeholder="Enter keywords separated by commas..."
                                        rows={3}
                                        className="input"
                                        required
                                    />
                                    <p className="mt-1 text-sm text-gray-500">
                                        Enter relevant keywords to search for. Separate multiple keywords with commas.
                                    </p>
                                </div>

                                {/* Max Results */}
                                <div>
                                    <label htmlFor="max_results" className="block text-sm font-medium text-gray-700 mb-2">
                                        Maximum Results
                                    </label>
                                    <input
                                        type="number"
                                        id="max_results"
                                        value={formData.max_results}
                                        onChange={(e) => setFormData(prev => ({ ...prev, max_results: parseInt(e.target.value) }))}
                                        min="1"
                                        max="100"
                                        className="input"
                                        required
                                    />
                                    <p className="mt-1 text-sm text-gray-500">
                                        Maximum number of results to collect (1-100)
                                    </p>
                                </div>

                                {/* Submit Button */}
                                <div>
                                    <button
                                        type="submit"
                                        disabled={createJobMutation.isPending}
                                        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        {createJobMutation.isPending ? (
                                            <>
                                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                                Creating Job...
                                            </>
                                        ) : (
                                            <>
                                                <Search className="w-4 h-4 mr-2" />
                                                Start Scraping
                                            </>
                                        )}
                                    </button>
                                </div>
                            </form>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    )
}
