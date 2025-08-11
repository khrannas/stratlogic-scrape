'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import { ScrapingJob, ScrapingRequest, Artifact } from '@/types'
import { useRouter } from 'next/navigation'

export function useJobs(page = 1, size = 20) {
  return useQuery({
    queryKey: ['jobs', page, size],
    queryFn: () => apiClient.getJobs(page, size),
    staleTime: 30 * 1000, // 30 seconds for real-time updates
  })
}

export function useJob(id: string) {
  return useQuery({
    queryKey: ['job', id],
    queryFn: () => apiClient.getJob(id),
    enabled: !!id,
    staleTime: 10 * 1000, // 10 seconds for real-time updates
    refetchInterval: 5000, // Refetch every 5 seconds for active jobs
  })
}

export function useJobArtifacts(jobId: string) {
  return useQuery({
    queryKey: ['job-artifacts', jobId],
    queryFn: () => apiClient.getJobArtifacts(jobId),
    enabled: !!jobId,
    staleTime: 60 * 1000, // 1 minute
  })
}

export function useCreateJob() {
  const queryClient = useQueryClient()
  const router = useRouter()

  return useMutation({
    mutationFn: (data: ScrapingRequest) => apiClient.createJob(data),
    onSuccess: (job) => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      router.push(`/jobs/${job.id}`)
    },
    onError: (error) => {
      console.error('Failed to create job:', error)
    },
  })
}

export function useCancelJob() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => apiClient.cancelJob(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      queryClient.invalidateQueries({ queryKey: ['job', id] })
    },
    onError: (error) => {
      console.error('Failed to cancel job:', error)
    },
  })
}
