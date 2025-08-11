'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useCreateJob } from '@/hooks/use-jobs'
import { Search, Globe, FileText, Building } from 'lucide-react'

const scrapingSchema = z.object({
  keywords: z.string().min(1, 'Keywords are required'),
  scraperType: z.enum(['web', 'paper', 'government']),
  maxResults: z.number().min(1).max(100).default(10),
})

type ScrapingFormData = z.infer<typeof scrapingSchema>

export function ScrapingRequestForm() {
  const { mutate: createJob, isPending } = useCreateJob()

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<ScrapingFormData>({
    resolver: zodResolver(scrapingSchema),
    defaultValues: {
      scraperType: 'web',
      maxResults: 10,
    },
  })

  const selectedType = watch('scraperType')

  const onSubmit = (data: ScrapingFormData) => {
    createJob({
      keywords: data.keywords.split(',').map(k => k.trim()).filter(Boolean),
      scraperType: data.scraperType,
      maxResults: data.maxResults,
    })
  }

  const scraperTypes = [
    {
      value: 'web',
      label: 'Web Scraper',
      description: 'Search and scrape web content from search engines',
      icon: Globe,
      color: 'bg-blue-100 text-blue-600',
    },
    {
      value: 'paper',
      label: 'Paper Scraper',
      description: 'Search academic papers from arXiv and other sources',
      icon: FileText,
      color: 'bg-green-100 text-green-600',
    },
    {
      value: 'government',
      label: 'Government Scraper',
      description: 'Search government documents and publications',
      icon: Building,
      color: 'bg-purple-100 text-purple-600',
    },
  ]

  return (
    <div className="max-w-2xl mx-auto">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
        {/* Keywords Input */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Keywords (comma-separated)
          </label>
          <textarea
            {...register('keywords')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            rows={3}
            placeholder="Enter keywords separated by commas, e.g., machine learning, artificial intelligence, data science"
          />
          {errors.keywords && (
            <p className="mt-1 text-sm text-red-600">{errors.keywords.message}</p>
          )}
        </div>

        {/* Scraper Type Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-4">
            Scraper Type
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {scraperTypes.map((type) => {
              const Icon = type.icon
              return (
                <label
                  key={type.value}
                  className={`relative cursor-pointer rounded-lg border-2 p-4 transition-colors ${
                    selectedType === type.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    {...register('scraperType')}
                    type="radio"
                    value={type.value}
                    className="sr-only"
                  />
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${type.color}`}>
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex-1">
                      <h3 className="text-sm font-medium text-gray-900">
                        {type.label}
                      </h3>
                      <p className="text-xs text-gray-500 mt-1">
                        {type.description}
                      </p>
                    </div>
                  </div>
                </label>
              )
            })}
          </div>
        </div>

        {/* Max Results */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Maximum Results
          </label>
          <input
            {...register('maxResults', { valueAsNumber: true })}
            type="number"
            min="1"
            max="100"
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {errors.maxResults && (
            <p className="mt-1 text-sm text-red-600">{errors.maxResults.message}</p>
          )}
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isPending}
          className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
        >
          <Search className="h-5 w-5" />
          <span>{isPending ? 'Creating Job...' : 'Start Scraping Job'}</span>
        </button>
      </form>
    </div>
  )
}
