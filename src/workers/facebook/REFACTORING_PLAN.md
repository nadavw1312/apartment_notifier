# Facebook Scraper Refactoring Plan

The current implementation of the Facebook scraper has several issues:
1. The `facebook_group_scraper.py` file is very large (1080+ lines)
2. There are unused methods (like `scroll_and_expand`)
3. The code mixes multiple responsibilities

## Proposed File Structure

```
src/workers/facebook/
├── __init__.py
├── facebook_scraper_manager.py (existing - manages multiple scrapers)
├── facebook_group_scraper.py (greatly reduced - main class only)
├── run_facebook_scrapers.py (existing)
├── shared_browser_manager.py (existing)
├── scraper_config.json (existing)
├── components/
│   ├── __init__.py
│   ├── auth.py (session/authentication handling)
│   ├── post_processor.py (processing posts after extraction)
│   ├── post_extractor.py (extract data from posts)
│   ├── data_saver.py (save data to database)
│   └── post_tracker.py (track processed posts)
└── utils/
    ├── __init__.py
    ├── html_parser.py (extraction functions from HTML)
    ├── regex_patterns.py (regex patterns used for extraction)
    └── text_filters.py (keyword filtering functions)
```

## Split by Functionality

1. **Authentication & Session Management** → `components/auth.py`
   - `save_facebook_session`
   - `create_facebook_session`
   - `load_session`

2. **Post Processing** → `components/post_processor.py`
   - `process_posts`, `process_posts_batch`
   - `process_batch_results`
   - LLM integration

3. **Post Extraction** → `components/post_extractor.py`
   - `extract_post_data_playwright` 
   - `extract_post_data_soup`
   - `expand_post_content`

4. **Data Storage** → `components/data_saver.py`
   - `save_apartment_data`

5. **Post Tracking** → `components/post_tracker.py`
   - `load_processed_post_ids`
   - Functions to manage the `processed_post_ids` set

6. **HTML & Text Utilities** → `utils/html_parser.py`
   - `extract_post_id`
   - HTML parsing helpers

7. **Text Filtering** → `utils/text_filters.py`
   - `is_apartment_post` 
   - Other content filtering functions

## Main Class Structure

The main `FacebookGroupScraper` class would be simplified to:
- Initialize components
- Set up browser/page
- Handle the scraping loop
- Coordinate the various components

## Migration Strategy

1. First, extract helper functions not bound to the class
2. Next, create the component modules and move relevant methods
3. Update imports and refactor the main class to use the components
4. Clean up unused code and variables
5. Ensure tests pass after each significant change

## Benefits

- **Improved Readability**: Each file has a single responsibility
- **Easier Maintenance**: Bug fixes and feature additions are isolated
- **Better Testability**: Components can be tested independently
- **Reduced Complexity**: Main class focuses on orchestration
- **Cleaner Development**: New contributors can understand the code more easily 