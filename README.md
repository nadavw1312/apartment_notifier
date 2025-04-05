# Apartment Notifier

This is a proof-of-concept application that notifies users via Telegram when a new apartment listing is uploaded. It supports a hybrid approach where you can choose to use PostgreSQL (SQL) or MongoDB (NoSQL) based on an environment variable.

## Features
- **User Registration:** Sign up via API and Telegram.
- **Apartment Listings:** New apartment posts are saved and processed.
variable.
- **Notifications:** Notifies users (starting with Telegram, expandable to SMS, Email, etc.).
- **Background Scheduler:** Scans Facebook groups for new posts (stub implementation).

## Setup
1. **Clone the repository** and create a virtual environment.
2. **Install dependencies:**
   ```bash
   poetry install

# 🧠 pgvector Setup on Windows for PostgreSQL 17

This guide walks you through installing and enabling the `pgvector` extension for PostgreSQL 17 on Windows. This is needed to store and query vector embeddings in your database (e.g., for similarity search in apartment listings).

---

## 📦 Prerequisites

- ✅ PostgreSQL 17 installed on Windows  
- ✅ Your database already created (e.g., `apartment_notifier`)
- ✅ Admin rights on your machine

---

## 1️⃣ Find Your PostgreSQL Installation Directory

Typically installed here:
C:\Program Files\PostgreSQL\17\



Ensure this folder contains subdirectories like `bin`, `lib`, `share\extension`, etc.

---

## 2️⃣ Download `pgvector` for Windows

1. Go to the official repo:  
   🔗 [https://github.com/andreiramani/pgvector_pgsql_windows/releases]

2. Find the latest release. Look for or download a **Windows-compatible** `.zip` or binary build (or a community-contributed one).

3. After downloading, extract it and ensure you have these files:
   - `vector.control`
   - `vector--0.5.0.sql` (or similar)
   - `vector.dll`

---

## 3️⃣ Install the Extension into PostgreSQL

Move files into the correct locations:

| File(s)          | Destination Path                                      |
|------------------|--------------------------------------------------------|
| `.control`, `.sql` | `C:\Program Files\PostgreSQL\17\share\extension\`     |
| `.dll`           | `C:\Program Files\PostgreSQL\17\lib\`                  |

⚠️ You may need admin privileges to write into these directories.

---

## 4️⃣ Restart PostgreSQL Service (Optional)

If the service was running before, restart it:

```powershell
Restart-Service postgresql-x64-17

## 5️⃣ Create the Extension in Your DB
Open psql using the right port (replace 5433 if using another port):

& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -d apartment_notifier -p 5433

Then in the prompt:

CREATE EXTENSION IF NOT EXISTS vector;


```

# Facebook Group Scraper

A multi-user, multi-group Facebook scraper system that allows for efficient scraping of apartment listings from Facebook groups. The system uses a configuration-based approach to manage different users, their Facebook sessions, and the groups they need to monitor.

## Features

- **Multi-user support**: Each user can have their own Facebook session stored in the database
- **Multi-group scraping**: Run scrapers for multiple Facebook groups in parallel
- **Configuration-based**: Easy to configure through a JSON file
- **Batch processing**: Process posts in batches for efficiency
- **Apartment data extraction**: Extract structured data from apartment posts using LLM
- **Database integration**: Store scraped data and sessions in a SQL database

## Architecture

The system follows SOLID principles with a modular architecture:

- `FacebookGroupScraper`: Core class responsible for scraping a single Facebook group
- `FacebookScraperManager`: Manager class that handles multiple users and their group configurations
- `ScraperUserService`: Database service for storing and retrieving user sessions
- Configuration system: Two-level configuration with system defaults and group-specific settings

## Setup

1. Create a configuration file at `src/workers/facebook/scraper_config.json` using the template below
2. Set up Facebook credentials for each user, or leave password blank for manual login
3. Configure the groups to scrape for each user
4. Run the scraper using the runner script

## Configuration

The configuration file (`src/workers/facebook/scraper_config.json`) has the following structure:

```json
{
  "users": [
    {
      "email": "your_email@example.com",
      "password": "your_password",
      "active": true,
      "groups": [
        {
          "group_id": "333022240594651",
          "name": "Tel Aviv Apartments",
          "config": {
            "fetch_interval": 10,
            "scroll_times": 5
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

### Configuration Options

- **users**: List of user configurations
  - **email**: User's email address (primary key)
  - **password**: Facebook login password (optional)
  - **active**: Whether this user is active
  - **groups**: List of Facebook groups to scrape
    - **group_id**: Facebook group ID
    - **name**: Display name for the group
    - **config**: Group-specific configuration (overrides system defaults)
- **system_defaults**: Default configuration values for all groups

Configuration is applied in layers:
1. System defaults (base)
2. Group-specific config (overrides system defaults)

## Usage

### Running the Scraper

To run the scraper for all active users from the config file:

```bash
python src/workers/facebook/run_facebook_scrapers.py
```

To run the scraper for all active users from the database:

```bash
python src/workers/facebook/run_facebook_scrapers.py --use-db
```

To run the scraper for a specific user:

```bash
python src/workers/facebook/run_facebook_scrapers.py --user your_email@example.com
```

With a custom configuration file:

```bash
python src/workers/facebook/run_facebook_scrapers.py --config custom_config.json
```

Limit the number of scraping cycles:

```bash
python src/workers/facebook/run_facebook_scrapers.py --cycles 5
```

### First Run

On the first run, if no session exists in the database for a user:
1. A temporary session file is created
2. A browser window is opened
3. Facebook login occurs (automatically if credentials provided, or manually)
4. The session is saved to the database
5. The temporary file is deleted

### Database Schema

The scraper uses a database table to store user sessions:

```sql
CREATE TABLE facebook_scraper_users (
    email VARCHAR(255) PRIMARY KEY,
    password VARCHAR(255),
    session_data TEXT,
    last_login VARCHAR(255),
    is_active VARCHAR(10) DEFAULT 'true'
);
```

## Development

### Adding a New User

To add a new user:
1. Add an entry to the `users` array in the configuration file, or
2. Insert a new record into the `facebook_scraper_users` table

### Adding New Groups to a User

To add a new group to an existing user, add an entry to the user's `groups` array with the group ID and optional configuration.

