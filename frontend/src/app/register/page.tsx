'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/use-auth'
import { RegisterForm } from '@/components/auth/register-form'
import Link from 'next/link'

export default function RegisterPage() {
  const { isAuthenticated, isLoadingUser } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoadingUser && isAuthenticated) {
      router.push('/dashboard')
    }
  }, [isAuthenticated, isLoadingUser, router])

  if (isLoadingUser) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (isAuthenticated) {
    return null
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Or{' '}
            <Link
              href="/login"
              className="font-medium text-blue-600 hover:text-blue-500"
            >
              sign in to your existing account
            </Link>
          </p>
        </div>

        <RegisterForm />
      </div>
    </div>
  )
}
