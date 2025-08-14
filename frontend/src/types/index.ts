// User types
export interface User {
    id: string
    email: string
    username: string
    role: 'admin' | 'user'
    is_active: boolean
    created_at: string
    updated_at: string
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

// Job types
export interface Job {
    id: string
    user_id: string
    job_type: 'web_scraper' | 'paper_scraper' | 'government_scraper'
    keywords: string[]
    status: 'pending' | 'running' | 'completed' | 'failed'
    progress: number
    total_items: number
    completed_items: number
    created_at: string
    updated_at: string
    started_at?: string
    completed_at?: string
    error_message?: string
}

// Specific scraper request types
export interface WebScraperRequest {
    keywords: string[]
    max_results_per_keyword?: number
    search_engines?: string[]
    expand_keywords?: boolean
    extract_images?: boolean
    extract_links?: boolean
}

export interface PaperScraperRequest {
    query: string
    max_results?: number
    sources?: string[]
    extract_pdfs?: boolean
    analyze_content?: boolean
    download_pdfs?: boolean
}

export interface GovernmentScraperRequest {
    keywords: string[]
    sources?: string[]
    max_documents_per_keyword?: number
    process_documents?: boolean
    analyze_content?: boolean
}

// Legacy type for backward compatibility
export interface CreateJobRequest {
    job_type: 'web_scraper' | 'paper_scraper' | 'government_scraper'
    keywords: string[]
    max_results?: number
}

// Artifact types
export interface Artifact {
    id: string
    job_id: string
    title: string
    content: string
    url?: string
    source_type: 'web' | 'paper' | 'government'
    metadata: Record<string, any>
    created_at: string
    updated_at: string
}

// API Response types
export interface ApiResponse<T> {
    data: T
    message?: string
    status: string
}

export interface PaginatedResponse<T> {
    data: T[]
    total: number
    page: number
    size: number
    pages: number
}

// Form types
export interface ScrapingFormData {
    job_type: 'web_scraper' | 'paper_scraper' | 'government_scraper'
    keywords: string
    max_results: number
}

// Filter types
export interface DocumentFilters {
    search?: string
    source_type?: 'web' | 'paper' | 'government'
    date_from?: string
    date_to?: string
    page?: number
    size?: number
}
