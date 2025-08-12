"""
Tests for ContentExtractor component
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from bs4 import BeautifulSoup
from src.scrapers.web_scraper import ContentExtractor


class TestContentExtractor:
    """Test ContentExtractor functionality"""

    @pytest.fixture
    def content_extractor(self):
        """Create ContentExtractor instance"""
        return ContentExtractor()

    @pytest.fixture
    def mock_page(self):
        """Mock page for testing"""
        page = Mock()
        page.content = AsyncMock(return_value="""
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test description">
                <meta property="og:title" content="OG Title">
                <meta property="og:description" content="OG Description">
                <meta name="author" content="Test Author">
                <meta name="keywords" content="test, web, scraping">
            </head>
            <body>
                <h1>Main Title</h1>
                <p>This is some content with <a href="https://example.com">a link</a>.</p>
                <img src="https://example.com/image.jpg" alt="Test image" width="100" height="100">
                <img src="/relative/image2.jpg" alt="Relative image">
                <script>console.log('test');</script>
                <style>.test { color: red; }</style>
            </body>
        </html>
        """)
        return page

    def test_initialization(self, content_extractor):
        """Test ContentExtractor initialization"""
        assert len(content_extractor.noise_patterns) > 0
        assert len(content_extractor.text_cleanup_patterns) > 0

    @pytest.mark.asyncio
    async def test_extract_content(self, content_extractor, mock_page):
        """Test content extraction"""
        content = await content_extractor.extract_content(mock_page, "https://example.com")

        assert content["url"] == "https://example.com"
        assert "title" in content
        assert "text_content" in content
        assert "content_hash" in content
        assert "word_count" in content
        assert "extraction_timestamp" in content
        assert "metadata" in content
        assert "images" in content
        assert "links" in content

    def test_extract_title(self, content_extractor):
        """Test title extraction"""
        # Test with OG title
        html = '<meta property="og:title" content="OG Title">'
        soup = BeautifulSoup(html, 'html.parser')
        title = content_extractor._extract_title(soup)
        assert title == "OG Title"

        # Test with regular title
        html = '<title>Regular Title</title>'
        soup = BeautifulSoup(html, 'html.parser')
        title = content_extractor._extract_title(soup)
        assert title == "Regular Title"

        # Test with h1 fallback
        html = '<h1>H1 Title</h1>'
        soup = BeautifulSoup(html, 'html.parser')
        title = content_extractor._extract_title(soup)
        assert title == "H1 Title"

    def test_extract_description(self, content_extractor):
        """Test description extraction"""
        # Test with meta description
        html = '<meta name="description" content="Meta description">'
        soup = BeautifulSoup(html, 'html.parser')
        desc = content_extractor._extract_description(soup)
        assert desc == "Meta description"

        # Test with OG description
        html = '<meta property="og:description" content="OG description">'
        soup = BeautifulSoup(html, 'html.parser')
        desc = content_extractor._extract_description(soup)
        assert desc == "OG description"

    def test_extract_text(self, content_extractor):
        """Test text extraction"""
        html = """
        <body>
            <h1>Title</h1>
            <p>This is some content.</p>
            <script>console.log('test');</script>
            <style>.test { color: red; }</style>
            <nav>Navigation</nav>
            <footer>Footer</footer>
        </body>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = content_extractor._extract_text(soup)

        assert "Title" in text
        assert "This is some content" in text
        assert "console.log" not in text  # Script should be removed
        assert ".test" not in text  # Style should be removed
        assert "Navigation" not in text  # Nav should be removed
        assert "Footer" not in text  # Footer should be removed

    def test_extract_images(self, content_extractor):
        """Test image extraction"""
        html = """
        <img src="https://example.com/image1.jpg" alt="Image 1" width="100" height="100">
        <img src="/relative/image2.jpg" alt="Image 2">
        <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==" alt="Data URL">
        """
        soup = BeautifulSoup(html, 'html.parser')
        images = content_extractor._extract_images(soup, "https://example.com")

        assert len(images) == 3
        assert images[0]["src"] == "https://example.com/image1.jpg"
        assert images[0]["alt"] == "Image 1"
        assert images[0]["width"] == "100"
        assert images[0]["height"] == "100"
        assert images[1]["src"] == "https://example.com/relative/image2.jpg"
        assert images[2]["src"].startswith("data:image/png;base64,")

    def test_extract_links(self, content_extractor):
        """Test link extraction"""
        html = """
        <a href="https://example.com/page1">Link 1</a>
        <a href="/relative/page2" title="Link 2">Link 2</a>
        <a href="#anchor">Anchor</a>
        <a href="javascript:void(0)">JS Link</a>
        <a href="mailto:test@example.com">Email</a>
        <a href="tel:+1234567890">Phone</a>
        """
        soup = BeautifulSoup(html, 'html.parser')
        links = content_extractor._extract_links(soup, "https://example.com")

        assert len(links) == 2  # Should exclude anchor, JS, email, and phone links
        assert links[0]["url"] == "https://example.com/page1"
        assert links[0]["text"] == "Link 1"
        assert links[1]["url"] == "https://example.com/relative/page2"
        assert links[1]["title"] == "Link 2"

    def test_clean_text(self, content_extractor):
        """Test text cleaning"""
        dirty_text = "  This   is   dirty   text  \n\n  with   extra   spaces  "
        cleaned_text = content_extractor._clean_text(dirty_text)

        assert "   " not in cleaned_text  # No multiple spaces
        assert cleaned_text.startswith("This")  # No leading spaces
        assert cleaned_text.endswith("spaces")  # No trailing spaces

    def test_content_validation(self, content_extractor):
        """Test content validation"""
        # Valid content
        valid_content = {
            "url": "https://example.com",
            "title": "Example Title",
            "text_content": "This is some content with enough words to pass validation."
        }
        assert content_extractor.validate_content(valid_content) is True

        # Invalid content - missing fields
        invalid_content = {
            "url": "https://example.com",
            "title": "Example Title"
            # Missing text_content
        }
        assert content_extractor.validate_content(invalid_content) is False

        # Invalid content - too short
        short_content = {
            "url": "https://example.com",
            "title": "Example Title",
            "text_content": "Too short"
        }
        assert content_extractor.validate_content(short_content) is False

    def test_extract_metadata(self, content_extractor):
        """Test metadata extraction"""
        html = """
        <meta name="author" content="Test Author">
        <meta name="keywords" content="test, web, scraping">
        <meta property="article:published_time" content="2023-01-01T00:00:00Z">
        <html lang="en">
        """
        soup = BeautifulSoup(html, 'html.parser')
        metadata = content_extractor._extract_metadata(soup, "https://example.com")

        assert metadata["url"] == "https://example.com"
        assert metadata["domain"] == "example.com"
        assert metadata["author"] == "Test Author"
        assert "test" in metadata["keywords"]
        assert "web" in metadata["keywords"]

    def test_extract_author(self, content_extractor):
        """Test author extraction"""
        # Test with meta author
        html = '<meta name="author" content="Test Author">'
        soup = BeautifulSoup(html, 'html.parser')
        author = content_extractor._extract_author(soup)
        assert author == "Test Author"

        # Test with no author
        html = '<html></html>'
        soup = BeautifulSoup(html, 'html.parser')
        author = content_extractor._extract_author(soup)
        assert author == ""

    def test_extract_keywords(self, content_extractor):
        """Test keywords extraction"""
        # Test with meta keywords
        html = '<meta name="keywords" content="test, web, scraping">'
        soup = BeautifulSoup(html, 'html.parser')
        keywords = content_extractor._extract_keywords(soup)
        assert "test" in keywords
        assert "web" in keywords
        assert "scraping" in keywords

        # Test with no keywords
        html = '<html></html>'
        soup = BeautifulSoup(html, 'html.parser')
        keywords = content_extractor._extract_keywords(soup)
        assert keywords == []

    def test_detect_language(self, content_extractor):
        """Test language detection"""
        # Test with html lang attribute
        html = '<html lang="en"></html>'
        soup = BeautifulSoup(html, 'html.parser')
        lang = content_extractor._detect_language(soup)
        assert lang == "en"

        # Test with no language
        html = '<html></html>'
        soup = BeautifulSoup(html, 'html.parser')
        lang = content_extractor._detect_language(soup)
        assert lang == ""

    @pytest.mark.asyncio
    async def test_extract_content_error_handling(self, content_extractor):
        """Test error handling in content extraction"""
        mock_page = Mock()
        mock_page.content = AsyncMock(side_effect=Exception("Content error"))

        content = await content_extractor.extract_content(mock_page, "https://example.com")
        assert content == {}

    def test_noise_removal(self, content_extractor):
        """Test noise pattern removal"""
        html = """
        <script>console.log('test');</script>
        <style>.test { color: red; }</style>
        <nav>Navigation</nav>
        <footer>Footer</footer>
        <div class="ad">Advertisement</div>
        <div id="ad">Another ad</div>
        <!-- Comment -->
        <p>Real content</p>
        """
        soup = BeautifulSoup(html, 'html.parser')
        text = content_extractor._extract_text(soup)

        # Should only contain real content
        assert "Real content" in text
        assert "console.log" not in text
        assert ".test" not in text
        assert "Navigation" not in text
        assert "Footer" not in text
        assert "Advertisement" not in text
        assert "Comment" not in text
