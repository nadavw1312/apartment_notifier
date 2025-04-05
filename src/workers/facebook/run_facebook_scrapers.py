#!/usr/bin/env python3
"""
Runner script for Facebook Group Scrapers.
This script loads the configuration from the JSON file and runs the scrapers.
"""

import argparse
import asyncio
import os
from pathlib import Path
from src.workers.facebook.facebook_scraper_manager import FacebookScraperManager

DEFAULT_CONFIG_PATH = "src/workers/facebook/scraper_config.json"

async def run_scrapers(config_path=None, user_email=None, max_cycles=None, use_db=False):
    """
    Run Facebook group scrapers based on configuration
    
    Args:
        config_path: Optional path to configuration file
        user_email: Optional user email to run scrapers for specific user only
        max_cycles: Optional maximum number of cycles to run
        use_db: Whether to use database users instead of config file users
    """
    # Use specified config path or default
    config_path = config_path or DEFAULT_CONFIG_PATH
    
    # Check if config file exists
    if not os.path.exists(config_path):
        print(f"❌ Config file not found at: {config_path}")
        return
        
    # Create the scraper manager
    manager = FacebookScraperManager(config_path)
    
    if use_db:
        # Run scrapers for all active users in the database
        print("🚀 Running scrapers for all active users from database")
        await manager.run_db_users(max_cycles)
    elif user_email:
        # Run scrapers for specific user
        user_configs = [u for u in manager.users if u.email == user_email and u.active]
        if not user_configs:
            print(f"❌ No active user found with email: {user_email}")
            return
            
        user = user_configs[0]
        print(f"🚀 Running scrapers for user: {user.email}")
        await manager.run_user_scrapers(user, max_cycles)
    else:
        # Run scrapers for all active users in the config
        print("🚀 Running scrapers for all active users from config")
        await manager.run_all_active_users(max_cycles)

def main():
    """Parse command line arguments and run scrapers"""
    parser = argparse.ArgumentParser(description="Run Facebook Group Scrapers")
    
    parser.add_argument(
        "--config", 
        type=str, 
        help=f"Path to configuration file (default: {DEFAULT_CONFIG_PATH})"
    )
    
    parser.add_argument(
        "--user", 
        type=str, 
        help="Run scrapers for specific user email only"
    )
    
    parser.add_argument(
        "--cycles", 
        type=int, 
        help="Maximum number of fetch cycles to run"
    )
    
    parser.add_argument(
        "--use-db",
        action="store_true",
        help="Use users from database instead of config file"
    )
    
    args = parser.parse_args()
    
    # Run the scrapers with provided options
    asyncio.run(run_scrapers(
        config_path=args.config,
        user_email=args.user,
        max_cycles=args.cycles,
        use_db=args.use_db
    ))

if __name__ == "__main__":
    main() 