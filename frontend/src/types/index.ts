export interface User {
  id: string
  email: string
  username: string
  role: 'ADMIN' | 'USER' | 'VIEWER' | 'MODERATOR'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Document {
  id: string
  title: string
  content: string
  source_url?: string
  source_type: 'web' | 'paper' | 'government'
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

export interface ScrapingJob {
  id: string
  user_id: string
  keywords: string[]
  scraper_type: 'web' | 'paper' | 'government'
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  results_count?: number
  error_message?: string
  created_at: string
  updated_at: string
}

export interface Artifact {
  id: string
  job_id: string
  title: string
  content: string
  source_url?: string
  source_type: 'web' | 'paper' | 'government'
  metadata: Record<string, any>
  file_path?: string
  file_size?: number
  created_at: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface RegisterRequest {
  email: string
  username: string
  password: string
}

export interface ScrapingRequest {
  keywords: string[]
  scraper_type: 'web' | 'paper' | 'government'
  max_results?: number
  additional_config?: Record<string, any>
}

export interface ApiResponse<T> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}
