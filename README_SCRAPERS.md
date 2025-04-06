# Unified Web Scraper System

This system allows running multiple web scraper managers from a single coordinating runner. It currently supports Facebook group scrapers and is designed to be extended for other platforms in the future.

## Architecture

The system uses a hierarchical approach:

1. **ScraperRunner** - Central coordinator that loads configuration and initializes platform managers
2. **Platform Managers** (e.g., `FacebookScraperManager`) - Each platform has its own manager that implements the `run_db_users()` method
3. **Individual Scrapers** - Managers create and coordinate individual scrapers for specific sources

This architecture makes it easy to add new platforms by creating new manager classes that follow the same interface pattern.

## Getting Started

### 1. Configuration

The system uses a JSON configuration file located at `config/scraper_config.json`. Here's an example of the configuration structure:

```json
{
  "global": {
    "headless": false,
    "fetch_interval": 300,
    "max_items_per_cycle": 30
  },
  "facebook": {
    "enabled": true,
    "users": [
      {
        "email": "user@example.com",
        "password": "password",
        "active": true,
        "groups": [
          {
            "group_id": "123456789",
            "name": "Tel Aviv Apartments",
            "config": {
              "scroll_times": 3
            }
          }
        ]
      }
    ],
    "defaults": {
      "scroll_times": 2,
      "batch_size": 10,
      "new_posts_only": true
    }
  }
}
```

#### Key Components:

- `global`: Settings that apply to all platforms
- Platform-specific sections (e.g., `facebook`):
  - `enabled`: Whether this platform's manager should be activated
  - `users`: List of users who can access the platform
  - `defaults`: Default settings for the platform

### 2. Running the System

To run all enabled platform managers:

```bash
python -m src.workers.scraper_runner
```

The system automatically handles:
- Initializing all enabled platform managers
- Running each manager's `run_db_users()` method
- Cleaning up resources properly when done

## Adding New Scraper Platforms

To add a new scraper platform:

1. Create a new platform manager class that extends `BaseScraperManager`
2. Implement all required methods, especially `run_db_users()`
3. Add the manager import to `scraper_runner.py`
4. Add initialization logic in the `initialize_managers` method
5. Add a new section to the configuration file template

For example, to add "Twitter" as a new platform:

```python
# In scraper_runner.py
from src.workers.scrappers.twitter.twitter_scraper_manager import TwitterScraperManager

# Then in initialize_managers():
if self.config.get("twitter", {}).get("enabled", False):
    try:
        twitter_manager = TwitterScraperManager()
        self.managers.append(twitter_manager)
        print("✅ Added Twitter scraper manager")
    except Exception as e:
        print(f"⚠️ Error initializing Twitter scraper manager: {e}")
```

## Configuration Reference

### Global Settings

- `headless`: Run browsers in headless mode (no visible UI)
- `fetch_interval`: Time between scraper cycles in seconds
- `max_items_per_cycle`: Maximum number of items to process per cycle

### Facebook Settings

- `defaults.scroll_times`: Number of times to scroll the page to load more content
- `defaults.batch_size`: Number of items to process in a batch
- `defaults.new_posts_only`: Only process posts that haven't been seen before

## Database Integration

Platform managers interact with the database to:
- Retrieve active users
- Store and retrieve session data
- Save scraped content

This integration allows the system to run continuously with persistent data between runs.

## Troubleshooting

### Authentication Issues

If you encounter authentication issues, the system will automatically attempt to create a new session. You might need to manually log in when the browser window opens.

### Configuration Errors

If the configuration file is missing or invalid, a default configuration will be created automatically. 