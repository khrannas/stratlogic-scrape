'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/use-auth'

export default function HomePage() {
  const { isAuthenticated, isLoadingUser } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoadingUser) {
      if (isAuthenticated) {
        router.push('/dashboard')
      } else {
        router.push('/login')
      }
    }
  }, [isAuthenticated, isLoadingUser, router])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          StratLogic Scraper
        </h1>
        <p className="text-gray-600">Loading...</p>
      </div>
    </div>
  )
}
