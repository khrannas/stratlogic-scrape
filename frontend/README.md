# StratLogic Frontend

A modern React/Next.js frontend for the StratLogic Scraping System.

## Features

- **Authentication**: JWT-based authentication with user management
- **Dashboard**: Overview of scraping jobs and statistics
- **Document Management**: Browse and search scraped documents
- **Job Management**: Create and monitor scraping jobs
- **Real-time Updates**: Live progress tracking for running jobs
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **React Query**: Data fetching and caching
- **Axios**: HTTP client for API requests
- **Lucide React**: Icon library
- **React Hook Form**: Form handling
- **Zod**: Schema validation
- **React Hot Toast**: Toast notifications

## Getting Started

### Prerequisites

- Node.js 18+
- npm, yarn, or pnpm
- Backend API running on `http://localhost:8000`

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp env.example .env.local
```

3. Start the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Environment Variables

Create a `.env.local` file with the following variables:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=StratLogic Scraper
```

## Project Structure

```
src/
├── app/                 # Next.js App Router pages
│   ├── login/          # Authentication pages
│   ├── documents/      # Document viewing
│   ├── scraping/       # Job creation
│   └── jobs/           # Job management
├── components/         # Reusable React components
├── hooks/             # Custom React hooks
├── lib/               # Utility functions and API client
└── types/             # TypeScript type definitions
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## API Integration

The frontend integrates with the following backend endpoints:

- **Authentication**: `/api/auth/*`
- **Users**: `/api/users/*`
- **Jobs**: `/api/jobs/*`
- **Artifacts**: `/api/artifacts/*`
- **Scrapers**: `/api/web_scraper/*`, `/api/paper_scraper/*`, `/api/government_scraper/*`

## Development

### Adding New Pages

1. Create a new directory in `src/app/`
2. Add a `page.tsx` file
3. Import and use the layout components (`Header`, `Sidebar`)

### Adding New Components

1. Create a new file in `src/components/`
2. Export the component as default
3. Import and use in pages

### API Calls

Use the `api` client from `src/lib/api.ts` for all HTTP requests:

```typescript
import api from '@/lib/api'

// GET request
const response = await api.get('/api/jobs')

// POST request
const response = await api.post('/api/jobs', data)
```

### State Management

Use React Query for server state management:

```typescript
import { useQuery, useMutation } from '@tanstack/react-query'

// Query data
const { data, isLoading } = useQuery({
  queryKey: ['jobs'],
  queryFn: () => api.get('/api/jobs').then(res => res.data)
})

// Mutate data
const mutation = useMutation({
  mutationFn: (data) => api.post('/api/jobs', data),
  onSuccess: () => {
    // Handle success
  }
})
```

## Deployment

### Build for Production

```bash
npm run build
npm run start
```

### Environment Variables for Production

Set the following environment variables in your production environment:

- `NEXT_PUBLIC_API_URL` - Backend API URL
- `NEXT_PUBLIC_APP_NAME` - Application name

## Contributing

1. Follow the existing code structure and patterns
2. Use TypeScript for all new code
3. Add proper error handling
4. Test your changes thoroughly
5. Update documentation as needed

## License

This project is part of the StratLogic Scraping System.
