'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { Search, Globe, FileText, Building } from 'lucide-react'
import api from '@/lib/api'
import { WebScraperRequest, PaperScraperRequest, GovernmentScraperRequest } from '@/types'
import { Header } from '@/components/header'
import { Sidebar } from '@/components/sidebar'
import { useAuth } from '@/hooks/use-auth'
import toast from 'react-hot-toast'

export default function ScrapingPage() {
    const { user, isAuthenticated } = useAuth()
    const router = useRouter()
    const queryClient = useQueryClient()

    const [formData, setFormData] = useState({
        job_type: 'web_scraper' as 'web_scraper' | 'paper_scraper' | 'government_scraper',
        keywords: '',
        max_results: 10,
        // Web scraper specific options
        search_engines: ['duckduckgo'],
        expand_keywords: true,
        extract_images: true,
        extract_links: true,
        // Paper scraper specific options
        sources: ['arxiv'],
        extract_pdfs: true,
        analyze_content: true,
        download_pdfs: true,
        // Government scraper specific options
        max_documents_per_keyword: 20,
        process_documents: true,
    })

    const createJobMutation = useMutation({
        mutationFn: async (data: { job_type: string; formData: any }) => {
            const { job_type, formData } = data

            let endpoint: string
            let requestData: any

            switch (job_type) {
                case 'web_scraper':
                    endpoint = '/api/v1/web-scraper/scrape'
                    requestData = {
                        keywords: formData.keywords.split(',').map((k: string) => k.trim()).filter((k: string) => k),
                        max_results_per_keyword: formData.max_results,
                        search_engines: formData.search_engines,
                        expand_keywords: formData.expand_keywords,
                        extract_images: formData.extract_images,
                        extract_links: formData.extract_links,
                    }
                    break
                case 'paper_scraper':
                    endpoint = '/api/v1/papers/search'
                    requestData = {
                        query: formData.keywords,
                        max_results: formData.max_results,
                        sources: formData.sources,
                        extract_pdfs: formData.extract_pdfs,
                        analyze_content: formData.analyze_content,
                        download_pdfs: formData.download_pdfs,
                    }
                    break
                case 'government_scraper':
                    endpoint = '/api/v1/government/search'
                    requestData = {
                        keywords: formData.keywords.split(',').map((k: string) => k.trim()).filter((k: string) => k),
                        sources: formData.sources,
                        max_documents_per_keyword: formData.max_documents_per_keyword,
                        process_documents: formData.process_documents,
                        analyze_content: formData.analyze_content,
                    }
                    break
                default:
                    throw new Error(`Unsupported job type: ${job_type}`)
            }

            const response = await api.post(endpoint, requestData)
            return response.data
        },
        onSuccess: (data) => {
            toast.success('Scraping job created successfully!')
            queryClient.invalidateQueries({ queryKey: ['jobs'] })
            // Navigate to job detail page using the job ID from the response
            const jobId = data.id || data.job_id
            router.push(`/jobs/${jobId}`)
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
            formData,
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

    // Render scraper-specific options based on selected job type
    const renderScraperSpecificOptions = () => {
        switch (formData.job_type) {
            case 'web_scraper':
                return (
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Search Engines
                            </label>
                            <div className="space-y-2">
                                {['duckduckgo', 'google', 'bing'].map((engine) => (
                                    <label key={engine} className="flex items-center">
                                        <input
                                            type="checkbox"
                                            checked={formData.search_engines.includes(engine)}
                                            onChange={(e) => {
                                                if (e.target.checked) {
                                                    setFormData(prev => ({
                                                        ...prev,
                                                        search_engines: [...prev.search_engines, engine]
                                                    }))
                                                } else {
                                                    setFormData(prev => ({
                                                        ...prev,
                                                        search_engines: prev.search_engines.filter(s => s !== engine)
                                                    }))
                                                }
                                            }}
                                            className="mr-2"
                                        />
                                        <span className="text-sm text-gray-700 capitalize">{engine}</span>
                                    </label>
                                ))}
                            </div>
                        </div>
                        <div className="space-y-2">
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    checked={formData.expand_keywords}
                                    onChange={(e) => setFormData(prev => ({ ...prev, expand_keywords: e.target.checked }))}
                                    className="mr-2"
                                />
                                <span className="text-sm text-gray-700">Expand keywords for better results</span>
                            </label>
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    checked={formData.extract_images}
                                    onChange={(e) => setFormData(prev => ({ ...prev, extract_images: e.target.checked }))}
                                    className="mr-2"
                                />
                                <span className="text-sm text-gray-700">Extract images</span>
                            </label>
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    checked={formData.extract_links}
                                    onChange={(e) => setFormData(prev => ({ ...prev, extract_links: e.target.checked }))}
                                    className="mr-2"
                                />
                                <span className="text-sm text-gray-700">Extract links</span>
                            </label>
                        </div>
                    </div>
                )
            case 'paper_scraper':
                return (
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Sources
                            </label>
                            <div className="space-y-2">
                                {['arxiv', 'crossref'].map((source) => (
                                    <label key={source} className="flex items-center">
                                        <input
                                            type="checkbox"
                                            checked={formData.sources.includes(source)}
                                            onChange={(e) => {
                                                if (e.target.checked) {
                                                    setFormData(prev => ({
                                                        ...prev,
                                                        sources: [...prev.sources, source]
                                                    }))
                                                } else {
                                                    setFormData(prev => ({
                                                        ...prev,
                                                        sources: prev.sources.filter(s => s !== source)
                                                    }))
                                                }
                                            }}
                                            className="mr-2"
                                        />
                                        <span className="text-sm text-gray-700 capitalize">{source}</span>
                                    </label>
                                ))}
                            </div>
                        </div>
                        <div className="space-y-2">
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    checked={formData.extract_pdfs}
                                    onChange={(e) => setFormData(prev => ({ ...prev, extract_pdfs: e.target.checked }))}
                                    className="mr-2"
                                />
                                <span className="text-sm text-gray-700">Extract PDF content</span>
                            </label>
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    checked={formData.analyze_content}
                                    onChange={(e) => setFormData(prev => ({ ...prev, analyze_content: e.target.checked }))}
                                    className="mr-2"
                                />
                                <span className="text-sm text-gray-700">Analyze content with AI</span>
                            </label>
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    checked={formData.download_pdfs}
                                    onChange={(e) => setFormData(prev => ({ ...prev, download_pdfs: e.target.checked }))}
                                    className="mr-2"
                                />
                                <span className="text-sm text-gray-700">Download PDFs</span>
                            </label>
                        </div>
                    </div>
                )
            case 'government_scraper':
                return (
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Sources
                            </label>
                            <div className="space-y-2">
                                {['websites', 'apis'].map((source) => (
                                    <label key={source} className="flex items-center">
                                        <input
                                            type="checkbox"
                                            checked={formData.sources.includes(source)}
                                            onChange={(e) => {
                                                if (e.target.checked) {
                                                    setFormData(prev => ({
                                                        ...prev,
                                                        sources: [...prev.sources, source]
                                                    }))
                                                } else {
                                                    setFormData(prev => ({
                                                        ...prev,
                                                        sources: prev.sources.filter(s => s !== source)
                                                    }))
                                                }
                                            }}
                                            className="mr-2"
                                        />
                                        <span className="text-sm text-gray-700 capitalize">{source}</span>
                                    </label>
                                ))}
                            </div>
                        </div>
                        <div>
                            <label htmlFor="max_documents_per_keyword" className="block text-sm font-medium text-gray-700 mb-2">
                                Max Documents per Keyword
                            </label>
                            <input
                                type="number"
                                id="max_documents_per_keyword"
                                value={formData.max_documents_per_keyword}
                                onChange={(e) => setFormData(prev => ({ ...prev, max_documents_per_keyword: parseInt(e.target.value) }))}
                                min="1"
                                max="100"
                                className="input"
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    checked={formData.process_documents}
                                    onChange={(e) => setFormData(prev => ({ ...prev, process_documents: e.target.checked }))}
                                    className="mr-2"
                                />
                                <span className="text-sm text-gray-700">Process document content</span>
                            </label>
                            <label className="flex items-center">
                                <input
                                    type="checkbox"
                                    checked={formData.analyze_content}
                                    onChange={(e) => setFormData(prev => ({ ...prev, analyze_content: e.target.checked }))}
                                    className="mr-2"
                                />
                                <span className="text-sm text-gray-700">Analyze content with AI</span>
                            </label>
                        </div>
                    </div>
                )
            default:
                return null
        }
    }

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

                                {/* Keywords/Query */}
                                <div>
                                    <label htmlFor="keywords" className="block text-sm font-medium text-gray-700 mb-2">
                                        {formData.job_type === 'paper_scraper' ? 'Search Query' : 'Keywords (comma-separated)'}
                                    </label>
                                    <textarea
                                        id="keywords"
                                        value={formData.keywords}
                                        onChange={(e) => setFormData(prev => ({ ...prev, keywords: e.target.value }))}
                                        placeholder={formData.job_type === 'paper_scraper' ? "Enter search query..." : "Enter keywords separated by commas..."}
                                        rows={3}
                                        className="input"
                                        required
                                    />
                                    <p className="mt-1 text-sm text-gray-500">
                                        {formData.job_type === 'paper_scraper'
                                            ? 'Enter a search query to find academic papers'
                                            : 'Enter relevant keywords to search for. Separate multiple keywords with commas.'
                                        }
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

                                {/* Scraper-specific options */}
                                {renderScraperSpecificOptions()}

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
