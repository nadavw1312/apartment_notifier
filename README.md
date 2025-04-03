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

