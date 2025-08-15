'use client'

import { useState, useEffect, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { User, LoginRequest, LoginResponse } from '@/types'
import toast from 'react-hot-toast'

// Safe localStorage access for SSR
const getToken = (): string | null => {
    if (typeof window !== 'undefined') {
        return localStorage.getItem('stratlogic_token')
    }
    return null
}

const setToken = (token: string): void => {
    if (typeof window !== 'undefined') {
        localStorage.setItem('stratlogic_token', token)
    }
}

const setRefreshToken = (token: string): void => {
    if (typeof window !== 'undefined') {
        localStorage.setItem('stratlogic_refresh_token', token)
    }
}

const removeTokens = (): void => {
    if (typeof window !== 'undefined') {
        localStorage.removeItem('stratlogic_token')
        localStorage.removeItem('stratlogic_refresh_token')
    }
}

export function useAuth() {
    const [user, setUser] = useState<User | null>(null)
    const [isClient, setIsClient] = useState(false)
    const queryClient = useQueryClient()

    // Ensure we're on the client side
    useEffect(() => {
        setIsClient(true)
    }, [])

    // Use React Query for user data with proper caching
    const { data: userData, isLoading, error } = useQuery({
        queryKey: ['user'],
        queryFn: async () => {
            const token = getToken()
            if (!token) {
                throw new Error('No token found')
            }
            const response = await api.get('/api/v1/auth/me')
            return response.data
        },
        enabled: isClient && !!getToken(),
        retry: false,
        staleTime: 5 * 60 * 1000, // 5 minutes
        gcTime: 10 * 60 * 1000, // 10 minutes (formerly cacheTime)
    })

    // Update local state when user data changes
    useEffect(() => {
        if (userData) {
            setUser(userData)
        } else if (error) {
            setUser(null)
            removeTokens()
        }
    }, [userData, error])

    const loginMutation = useMutation({
        mutationFn: async (credentials: LoginRequest) => {
            const response = await api.post<LoginResponse>('/api/v1/auth/login', credentials)
            return response.data
        },
        onSuccess: (data) => {
            setToken(data.access_token)
            setRefreshToken(data.refresh_token)
            setUser(data.user)
            // Invalidate and refetch user data
            queryClient.invalidateQueries({ queryKey: ['user'] })
            toast.success('Login successful!')
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Login failed')
        },
    })

    const logout = useCallback(() => {
        removeTokens()
        setUser(null)
        queryClient.clear()
        toast.success('Logged out successfully')
    }, [queryClient])

    const login = useCallback((email: string, password: string) => {
        return loginMutation.mutateAsync({ email, password })
    }, [loginMutation])

    return {
        user,
        isLoading: isLoading || loginMutation.isPending,
        isAuthenticated: !!user,
        login,
        logout,
        loginError: loginMutation.error,
    }
}
