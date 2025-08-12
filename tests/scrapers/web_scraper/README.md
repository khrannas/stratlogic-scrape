# Web Scraper Testing Documentation

## Overview

This directory contains comprehensive tests for the web scraper components. The testing suite covers all major components with both unit tests and integration tests.

## Test Structure

### Unit Tests

1. **`test_playwright_manager.py`** - Tests for PlaywrightManager
   - Browser pool management
   - Page creation and configuration
   - User agent rotation
   - Async context manager functionality
   - Error handling and cleanup

2. **`test_search_engines.py`** - Tests for SearchEngineScraper
   - Google search functionality
   - Bing search functionality
   - DuckDuckGo search functionality
   - Rate limiting
   - Error handling
   - Result filtering and validation

3. **`test_content_extractor.py`** - Tests for ContentExtractor
   - HTML content extraction
   - Title and description extraction
   - Text cleaning and normalization
   - Image and link extraction
   - Metadata extraction
   - Content validation

4. **`test_web_scraper_main.py`** - Tests for main WebScraper orchestrator
   - Complete scraping workflow
   - Job management integration
   - Storage integration
   - Error handling and recovery
   - URL validation and filtering
   - Duplicate removal

5. **`test_config.py`** - Tests for WebScraperSettings
   - Configuration validation
   - Default values
   - Custom settings
   - Environment variable loading
   - Configuration serialization

### Integration Tests

**`test_integration.py`** - Comprehensive integration tests
- Full scraping workflow with mocked dependencies
- Multiple search engine integration
- Content extraction pipeline
- Error recovery scenarios
- Performance testing
- Concurrent operations
- Data flow validation

### Shared Fixtures

**`conftest.py`** - Shared test fixtures and utilities
- Mock objects for all components
- Sample data for testing
- Async test support
- Common test configurations

## Test Coverage

### Components Tested

- ✅ **PlaywrightManager** - Browser automation and management
- ✅ **SearchEngineScraper** - Search engine integration (Google, Bing, DuckDuckGo)
- ✅ **ContentExtractor** - HTML parsing and content extraction
- ✅ **WebScraper** - Main orchestrator and workflow management
- ✅ **WebScraperSettings** - Configuration management

### Test Types

- ✅ **Unit Tests** - Individual component testing with mocked dependencies
- ✅ **Integration Tests** - End-to-end workflow testing
- ✅ **Error Handling Tests** - Exception scenarios and recovery
- ✅ **Performance Tests** - Timing and resource usage validation
- ✅ **Concurrent Tests** - Multi-threaded operation testing

## Running Tests

### Prerequisites

- Python 3.13+
- pytest
- pytest-asyncio
- Required dependencies from `requirements.txt`

### Running All Tests

```bash
# From project root
python -m pytest tests/scrapers/web_scraper/ -v

# Using the test runner
python tests/scrapers/web_scraper/run_tests.py
```

### Running Specific Test Categories

```bash
# Unit tests only
python -m pytest tests/scrapers/web_scraper/test_*.py -v

# Integration tests only
python -m pytest tests/scrapers/web_scraper/test_integration.py -v

# Specific component tests
python -m pytest tests/scrapers/web_scraper/test_playwright_manager.py -v
python -m pytest tests/scrapers/web_scraper/test_search_engines.py -v
python -m pytest tests/scrapers/web_scraper/test_content_extractor.py -v
python -m pytest tests/scrapers/web_scraper/test_web_scraper_main.py -v
python -m pytest tests/scrapers/web_scraper/test_config.py -v
```

### Running with Coverage

```bash
# Install coverage
pip install pytest-cov

# Run with coverage report
python -m pytest tests/scrapers/web_scraper/ --cov=src.scrapers.web_scraper --cov-report=html
```

## Test Data

### Sample HTML Content

Tests use realistic HTML content including:
- Meta tags (title, description, Open Graph)
- Structured content (headings, paragraphs, links)
- Images with various attributes
- Script and style elements for noise testing
- Various URL formats (absolute, relative, data URLs)

### Mock Responses

- Search engine results with realistic structure
- Content extraction results with full metadata
- Error scenarios and edge cases
- Performance timing data

## Mocking Strategy

### External Dependencies

- **Playwright** - Mocked browser and page objects
- **Search Engines** - Mocked HTTP responses and page content
- **Storage Services** - Mocked artifact creation and retrieval
- **Job Management** - Mocked job status updates and progress tracking

### Benefits

- Fast test execution (no network calls)
- Reliable test results (no external dependencies)
- Comprehensive error scenario testing
- Isolated component testing

## Test Patterns

### Async Testing

All async operations are properly tested using:
- `@pytest.mark.asyncio` decorator
- `AsyncMock` for async method mocking
- Proper event loop management

### Fixture Usage

- Shared fixtures for common test data
- Dependency injection for component testing
- Reusable mock objects

### Error Testing

- Exception handling validation
- Graceful degradation testing
- Recovery mechanism verification

## Quality Assurance

### Code Coverage

The test suite provides comprehensive coverage of:
- All public methods and properties
- Error handling paths
- Edge cases and boundary conditions
- Configuration validation

### Test Reliability

- Deterministic test results
- No external dependencies
- Proper cleanup and teardown
- Isolated test execution

## Future Enhancements

### Potential Additions

- **Real Network Tests** - Integration tests with actual websites (optional)
- **Performance Benchmarks** - Detailed performance profiling
- **Load Testing** - High-volume scraping scenarios
- **Security Testing** - Input validation and security edge cases

### Continuous Integration

- Automated test execution
- Coverage reporting
- Performance regression testing
- Security scanning

## Troubleshooting

### Common Issues

1. **Import Errors** - Ensure project root is in Python path
2. **Database Connection** - Tests use mocked dependencies, no database required
3. **Async Test Failures** - Check event loop configuration
4. **Mock Setup** - Verify mock objects are properly configured

### Debug Mode

```bash
# Run with detailed output
python -m pytest tests/scrapers/web_scraper/ -v -s --tb=long

# Run specific failing test
python -m pytest tests/scrapers/web_scraper/test_specific.py::test_specific_function -v -s
```

## Conclusion

The web scraper testing suite provides comprehensive coverage of all components with both unit and integration tests. The tests are designed to be fast, reliable, and maintainable, using proper mocking strategies to isolate components and ensure deterministic results.
