'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { LoginRequest, RegisterRequest, User } from '@/types'
import { useRouter } from 'next/navigation'

export function useAuth() {
  const queryClient = useQueryClient()
  const router = useRouter()

  // Get current user
  const { data: user, isLoading: isLoadingUser } = useQuery({
    queryKey: ['user'],
    queryFn: apiClient.getCurrentUser,
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: (data: LoginRequest) => apiClient.login(data),
    onSuccess: (data) => {
      queryClient.setQueryData(['user'], data.user)
      router.push('/dashboard')
    },
    onError: (error) => {
      console.error('Login failed:', error)
    },
  })

  // Register mutation
  const registerMutation = useMutation({
    mutationFn: (data: RegisterRequest) => apiClient.register(data),
    onSuccess: () => {
      router.push('/login?message=Registration successful. Please log in.')
    },
    onError: (error) => {
      console.error('Registration failed:', error)
    },
  })

  // Logout mutation
  const logoutMutation = useMutation({
    mutationFn: () => apiClient.logout(),
    onSuccess: () => {
      queryClient.clear()
      router.push('/login')
    },
    onError: (error) => {
      console.error('Logout failed:', error)
      // Clear local data even if logout fails
      queryClient.clear()
      router.push('/login')
    },
  })

  return {
    user,
    isLoadingUser,
    isAuthenticated: !!user,
    login: loginMutation.mutate,
    loginAsync: loginMutation.mutateAsync,
    isLoggingIn: loginMutation.isPending,
    register: registerMutation.mutate,
    registerAsync: registerMutation.mutateAsync,
    isRegistering: registerMutation.isPending,
    logout: logoutMutation.mutate,
    isLoggingOut: logoutMutation.isPending,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
  }
}
