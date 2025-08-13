export const config = {
    api: {
        baseUrl: process.env.NEXT_PUBLIC_API_URL || '',
        timeout: 30000,
    },
    auth: {
        tokenKey: 'stratlogic_token',
        refreshTokenKey: 'stratlogic_refresh_token',
    },
    features: {
        realTimeUpdates: true,
        documentPreview: true,
        advancedSearch: true,
    }
}
