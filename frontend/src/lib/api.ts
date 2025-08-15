import axios from 'axios'
import { config } from './config'

const api = axios.create({
    baseURL: config.api.baseUrl,
    timeout: config.api.timeout,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Safe localStorage access for SSR
const getToken = (): string | null => {
    if (typeof window !== 'undefined') {
        return localStorage.getItem('stratlogic_token')
    }
    return null
}

const removeTokens = (): void => {
    if (typeof window !== 'undefined') {
        localStorage.removeItem('stratlogic_token')
        localStorage.removeItem('stratlogic_refresh_token')
    }
}

// Request interceptor to add auth token
api.interceptors.request.use(
    (config) => {
        const token = getToken()
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response interceptor to handle auth errors
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            removeTokens()
            if (typeof window !== 'undefined') {
                window.location.href = '/login'
            }
        }
        return Promise.reject(error)
    }
)

export default api
