# Facebook Group Scraper

This module provides a system for scraping apartment rental posts from Facebook groups.

## Configuration

The system uses a configuration file `scraper_config.json` to define scraper users and their associated Facebook groups to scrape. The system will automatically sync this configuration with the database.

### Configuration File Structure

```json
{
  "users": [
    {
      "email": "example@example.com",
      "password": "your_password",
      "active": true,
      "groups": [
        {
          "group_id": "123456789",
          "name": "Example Group",
          "config": {
            "fetch_interval": 10,
            "scroll_times": 5,
            "batch_size": 10,
            "headless": false
          }
        }
      ]
    }
  ],
  "system_defaults": {
    "fetch_interval": 15,
    "scroll_times": 5,
    "num_posts_to_fetch": 10,
    "batch_size": 10,
    "headless": false
  }
}
```

## Usage

### Initialize Configuration

To initialize the configuration users in the database without running the scrapers:

```bash
python -m src.workers.facebook.facebook_scraper_manager init
```

This will:
1. Create users in the database if they don't exist
2. Update existing users' active status
3. Prepare the database for running scrapers

### Run Scrapers

To run the scraper for all active users:

```bash
python -m src.workers.facebook.facebook_scraper_manager
```

This will:
1. Synchronize configuration users with the database
2. Run scrapers for all active users

## Optimized Browser Usage

The scraper uses a sophisticated browser sharing approach for better efficiency:

- **User-Specific Browser Instances**: Each user gets their own dedicated Chrome browser instance
- **Tab-Based Sharing**: All groups for a specific user share the same browser but open in separate tabs
- **Session Isolation**: Different users maintain different sessions, ensuring proper authentication
- **Resource Efficiency**: Significantly reduces memory usage compared to one browser per group

This multi-level optimization allows:
1. Complete session isolation between users (different logins)
2. Efficient resource usage within each user's context
3. Better scalability for handling many groups across multiple users

## Session Management

The system stores Facebook session data directly in the database instead of temporary files. This makes it more robust and allows for better management of multiple user sessions. 