'use client'

import { useState, useEffect, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'
import { User, LoginRequest, LoginResponse } from '@/types'
import toast from 'react-hot-toast'

export function useAuth() {
    const [user, setUser] = useState<User | null>(null)
    const [isLoading, setIsLoading] = useState(true)
    const queryClient = useQueryClient()

    // Check if user is authenticated on mount
    useEffect(() => {
        const token = localStorage.getItem('stratlogic_token')
        if (token) {
            fetchUser()
        } else {
            setIsLoading(false)
        }
    }, [])

    const fetchUser = useCallback(async () => {
        try {
            const response = await api.get('/api/v1/auth/me')
            setUser(response.data)
        } catch (error) {
            console.error('Failed to fetch user:', error)
            localStorage.removeItem('stratlogic_token')
            localStorage.removeItem('stratlogic_refresh_token')
        } finally {
            setIsLoading(false)
        }
    }, [])

    const loginMutation = useMutation({
        mutationFn: async (credentials: LoginRequest) => {
            const response = await api.post<LoginResponse>('/api/v1/auth/login', credentials)
            return response.data
        },
        onSuccess: (data) => {
            localStorage.setItem('stratlogic_token', data.access_token)
            localStorage.setItem('stratlogic_refresh_token', data.refresh_token)
            setUser(data.user)
            toast.success('Login successful!')
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Login failed')
        },
    })

    const logout = useCallback(() => {
        localStorage.removeItem('stratlogic_token')
        localStorage.removeItem('stratlogic_refresh_token')
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
