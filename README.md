# StratLogic Scraping System

A comprehensive web scraping system designed to collect, process, and store data from multiple sources including web content, academic papers, and government documents.

## 🎯 Project Overview

This system provides a unified platform for scraping and storing various types of content with intelligent keyword expansion, metadata tagging, and scalable storage using MinIO.

## 🏗️ System Architecture

### Core Components

1. **Web Scraper Module**
   - Playwright-based web scraping
   - Search engine integration (Google, Bing, DuckDuckGo)
   - LLM-powered keyword expansion
   - Content extraction and processing

2. **Paper Scraper Module**
   - arXiv API integration for academic papers
   - Grobid for PDF processing and metadata extraction
   - CrossRef API for additional academic sources
   - Semantic Scholar API for paper recommendations

3. **Government Document Scraper Module**
   - Indonesian government website scraping
   - Document repository integration
   - PDF and document processing
   - Official API integration where available

4. **Storage & Metadata System**
   - MinIO object storage for artifacts
   - Comprehensive metadata tagging system
   - User management and access control
   - Search and retrieval capabilities

5. **API & Management Layer**
   - RESTful API for system interaction
   - User authentication and authorization
   - Job scheduling and monitoring
   - Analytics and reporting

## 🛠️ Technology Stack

### Core Technologies
- **Python 3.11+** - Main programming language
- **FastAPI** - Web framework for API
- **Playwright** - Web automation and scraping
- **MinIO** - Object storage
- **PostgreSQL** - Metadata and user management
- **Redis** - Caching and job queues

### Scraping Libraries
- **arxiv.py** - arXiv paper scraping (MIT licensed)
- **Grobid** - PDF processing and document analysis
- **BeautifulSoup4** - HTML parsing
- **Scrapy** - Web scraping framework
- **Selenium** - Alternative web automation

### AI/ML Integration
- **LiteLLM** - Unified LLM interface supporting multiple providers
- **OpenAI** - GPT-4, GPT-4o, and other OpenAI models
- **OpenRouter** - Cost-effective LLM access (GPT-4, Claude, etc.)
- **Google Gemini** - Free/cheap LLM for content analysis
- **Anthropic** - Claude models via OpenRouter
- **LangChain** - LLM orchestration
- **Transformers** - Text processing and analysis

### Frontend Technologies
- **React/Next.js** - Modern web frontend
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Styling and responsive design
- **React Query** - Data fetching and caching

### Additional Tools
- **Docker** - Containerization
- **Celery** - Task queue management
- **Prometheus** - Monitoring
- **Grafana** - Visualization

## 📁 Project Structure

```
stratlogic-scrape/
├── src/
│   ├── scrapers/
│   │   ├── web_scraper/
│   │   ├── paper_scraper/
│   │   └── government_scraper/
│   ├── storage/
│   │   ├── minio_client/
│   │   └── metadata_manager/
│   ├── api/
│   │   ├── routes/
│   │   └── middleware/
│   ├── core/
│   │   ├── config/
│   │   ├── models/
│   │   └── utils/
│   └── services/
│       ├── llm_service/
│       └── job_scheduler/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── utils/
│   ├── public/
│   └── package.json
├── tests/
├── docs/
├── docker/
├── scripts/
└── todo/
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- MinIO server
- PostgreSQL database
- Redis server

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd stratlogic-scrape
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Start services:
```bash
docker-compose up -d
```

6. Run migrations:
```bash
python scripts/migrate.py
```

7. Start the application:
```bash
python src/main.py
```

## 📊 Data Flow

1. **Input Processing**
   - User submits scraping request with keywords via frontend
   - LLM (OpenRouter/Gemini) expands keywords into related terms
   - System determines appropriate scrapers

2. **Content Collection**
   - Parallel scraping across multiple sources
   - Content extraction and cleaning
   - Metadata generation

3. **Storage & Indexing**
   - Artifacts stored in MinIO
   - Metadata stored in PostgreSQL
   - Full-text indexing for search

4. **Access & Retrieval**
   - Frontend interface for document viewing and search
   - API endpoints for data access
   - Real-time progress tracking
   - User permission management

## 🔧 Configuration

### Environment Variables
- `MINIO_ENDPOINT` - MinIO server endpoint
- `MINIO_ACCESS_KEY` - MinIO access key
- `MINIO_SECRET_KEY` - MinIO secret key
- `POSTGRES_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string

#### LLM Configuration
- `LLM_PROVIDER` - LLM provider (openai, gemini, openrouter, anthropic)
- `OPENAI_API_KEY` - OpenAI API key
- `OPENROUTER_API_KEY` - OpenRouter API key for cost-effective LLM access
- `GOOGLE_API_KEY` - Google API key for Gemini models
- `GEMINI_API_KEY` - Google Gemini API key (alternative to GOOGLE_API_KEY)
- `USE_LITELLM_PROXY` - Enable LiteLLM proxy (true/false)
- `LITELLM_PROXY_URL` - LiteLLM proxy URL (default: http://localhost:4000)
- `ARXIV_API_KEY` - arXiv API key (optional)

### Scraper Configuration
Each scraper module has its own configuration file:
- `config/web_scraper.yaml`
- `config/paper_scraper.yaml`
- `config/government_scraper.yaml`

### LiteLLM Configuration
The system uses LiteLLM for unified LLM access. You can configure it in two ways:

#### Direct Integration (Default)
Set your API keys in the environment variables and the system will use LiteLLM directly:
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key
```

#### LiteLLM Proxy (Optional)
For advanced features like model routing, caching, and observability:
1. Set `USE_LITELLM_PROXY=true` in your `.env` file
2. The LiteLLM proxy will be available at `http://localhost:4000`
3. Configure models in `litellm-config.yaml`

## 📈 Monitoring & Analytics

- **Scraping Metrics**: Success rates, response times, data volume
- **System Health**: Resource usage, error rates, uptime
- **User Analytics**: Usage patterns, popular keywords, data access
- **Content Analytics**: Source distribution, content types, quality metrics

## 🔒 Security & Privacy

- **Authentication**: JWT-based user authentication
- **Authorization**: Role-based access control
- **Data Privacy**: Private/public data segregation
- **Rate Limiting**: API rate limiting to prevent abuse
- **Audit Logging**: Comprehensive activity logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation in the `docs/` folder
- Review the troubleshooting guide

## 🔄 Roadmap

### Phase 1: Core Infrastructure
- [x] Project setup and architecture
- [ ] Basic web scraper implementation
- [ ] MinIO integration
- [ ] User management system

### Phase 2: Scraping Modules
- [ ] Paper scraper with arXiv integration
- [ ] Government document scraper
- [ ] Advanced web scraping features
- [ ] LLM keyword expansion (OpenRouter/Gemini)

### Phase 3: Frontend Development
- [ ] React/Next.js frontend application
- [ ] Document viewing and search interface
- [ ] Scraping request form and job management
- [ ] Real-time progress tracking dashboard

### Phase 4: Advanced Features
- [ ] Real-time monitoring
- [ ] Advanced analytics
- [ ] API rate limiting
- [ ] Performance optimization

### Phase 5: Scale & Production
- [ ] Docker containerization
- [ ] CI/CD pipeline
- [ ] Production deployment
- [ ] Documentation completion
