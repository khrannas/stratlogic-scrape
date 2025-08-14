# Playwright Stealth Integration

This document describes the integration of `playwright-stealth` into the StratLogic Scraping System to enhance bot detection avoidance capabilities.

## Overview

The web scraper now includes `playwright-stealth` integration to help avoid bot detection mechanisms. This library applies various stealth techniques to make automated browsers appear more like regular user browsers.

## Features

### Automatic Stealth Application
- All pages created through the PlaywrightManager automatically have stealth measures applied
- Configurable through the `enable_stealth` parameter
- No additional code required - stealth is applied transparently

### Stealth Techniques Applied
- **WebDriver Property**: Hides the `navigator.webdriver` property
- **User Agent**: Rotates and modifies user agents to appear more human-like
- **Browser Fingerprinting**: Masks automation-related properties
- **Plugin Detection**: Handles plugin enumeration to avoid detection
- **Language Settings**: Configures realistic language preferences
- **Hardware Concurrency**: Sets realistic CPU core counts
- **Device Memory**: Configures realistic memory values
- **Touch Points**: Sets appropriate touch capabilities
- **Chrome Runtime**: Masks Chrome automation properties

## Configuration

### Environment Variables
```bash
# Enable/disable stealth mode (default: true)
WEB_SCRAPER_ENABLE_STEALTH=true

# Other web scraper settings
WEB_SCRAPER_HEADLESS=true
WEB_SCRAPER_MAX_BROWSERS=5
WEB_SCRAPER_PROXY=null
```

### Code Configuration
```python
from scrapers.web_scraper.config import web_scraper_settings

# Check if stealth is enabled
print(f"Stealth enabled: {web_scraper_settings.enable_stealth}")
```

## Usage

### Basic Usage
```python
from scrapers.web_scraper.playwright_manager import PlaywrightManager

# Stealth is enabled by default
async with PlaywrightManager() as manager:
    browser = await manager.get_browser()
    page = await manager.create_page(browser)
    # Stealth measures are automatically applied
```

### Custom Configuration
```python
# Disable stealth if needed
async with PlaywrightManager(enable_stealth=False) as manager:
    # Regular Playwright without stealth
    pass

# Enable stealth explicitly
async with PlaywrightManager(enable_stealth=True) as manager:
    # Enhanced stealth mode
    pass
```

### Verification
```python
# Verify stealth measures are working
stealth_status = await manager.verify_stealth(page)
print(f"WebDriver hidden: {stealth_status.get('webdriver')}")
```

## Testing

### Test Script
Run the comprehensive test script to verify stealth functionality:

```bash
python scripts/test_stealth.py
```

This script will:
- Test stealth vs non-stealth modes
- Verify WebDriver property hiding
- Take screenshots for visual verification
- Compare browser fingerprinting

### API Testing
Test stealth through the API:

```bash
curl -X POST "http://localhost:8000/api/v1/web-scraper/test-stealth" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Manual Testing
Visit bot detection test sites:
- https://bot.sannysoft.com
- https://arh.antoinevastel.com/bots/areyouheadless
- https://intoli.com/blog/not-possible-to-block-chrome-headless/

## Installation

### Automatic Installation
```bash
python scripts/install_stealth.py
```

### Manual Installation
```bash
pip install playwright-stealth==1.0.5
playwright install chromium
```

## Troubleshooting

### Common Issues

1. **Import Error**: `ModuleNotFoundError: No module named 'playwright_stealth'`
   - Solution: Install the package with `pip install playwright-stealth==1.0.5`

2. **Stealth Not Working**: WebDriver property still visible
   - Check that `enable_stealth=True` in configuration
   - Verify the page was created after stealth initialization
   - Test with the verification method

3. **Performance Impact**: Slower page loading
   - Stealth measures add some overhead
   - Consider disabling for high-performance scraping needs
   - Use browser pooling to minimize initialization overhead

### Debug Mode
Enable debug logging to see stealth application:

```python
import logging
logging.getLogger('scrapers.web_scraper.playwright_manager').setLevel(logging.DEBUG)
```

## Best Practices

1. **Always Test**: Use the test script to verify stealth is working
2. **Monitor Detection**: Regularly check if sites are detecting automation
3. **Rotate Settings**: Use different user agents and configurations
4. **Respect Rate Limits**: Even with stealth, respect website rate limits
5. **Keep Updated**: Update playwright-stealth for latest evasion techniques

## Security Considerations

- Stealth measures are for legitimate scraping only
- Respect robots.txt and website terms of service
- Use appropriate delays between requests
- Consider using proxies for additional anonymity
- Monitor for changes in bot detection methods

## Performance Impact

Stealth measures add approximately 10-20% overhead to page loading times. This is acceptable for most use cases but should be considered for high-volume scraping.

## Future Enhancements

- Additional stealth techniques as they become available
- Machine learning-based fingerprint randomization
- Integration with proxy rotation services
- Advanced browser fingerprinting evasion
