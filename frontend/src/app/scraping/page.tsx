'use client'

import { ScrapingRequestForm } from '@/components/scraping/request-form'
import { Search, Globe, FileText, Building } from 'lucide-react'

export default function ScrapingPage() {
  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Create New Scraping Job
          </h1>
          <p className="text-gray-600">
            Start a new scraping job to collect documents from various sources.
          </p>
        </div>

        {/* Scraper Types Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Globe className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="ml-3 text-lg font-medium text-gray-900">Web Scraper</h3>
            </div>
            <p className="text-gray-600 text-sm">
              Search and scrape web content from Google, Bing, and DuckDuckGo. 
              Collect articles, blog posts, and web pages.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <div className="p-2 bg-green-100 rounded-lg">
                <FileText className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="ml-3 text-lg font-medium text-gray-900">Paper Scraper</h3>
            </div>
            <p className="text-gray-600 text-sm">
              Search academic papers from arXiv and other academic sources. 
              Extract full-text content and metadata.
            </p>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center mb-4">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Building className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="ml-3 text-lg font-medium text-gray-900">Government Scraper</h3>
            </div>
            <p className="text-gray-600 text-sm">
              Search government documents and publications. 
              Collect official reports, policies, and regulations.
            </p>
          </div>
        </div>

        {/* Scraping Form */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Job Configuration</h2>
          </div>
          <div className="p-6">
            <ScrapingRequestForm />
          </div>
        </div>
      </div>
    </div>
  )
}
