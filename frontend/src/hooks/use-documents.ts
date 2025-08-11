'use client'

import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { Document } from '@/types'

export function useDocuments(page = 1, size = 20, search?: string) {
  return useQuery({
    queryKey: ['documents', page, size, search],
    queryFn: () => apiClient.getDocuments(page, size, search),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useDocument(id: string) {
  return useQuery({
    queryKey: ['document', id],
    queryFn: () => apiClient.getDocument(id),
    enabled: !!id,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}
