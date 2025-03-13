#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
User data storage and management
"""

import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Path to user data file
USER_DATA_FILE = "data/users.json"

# In-memory storage for user data
users = {}

def load_user_data():
    """Load user data from JSON file"""
    global users
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r', encoding='utf-8') as file:
                users = json.load(file)
                logger.info(f"Loaded {len(users)} user records from file")
        else:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
            users = {}
            logger.info("No user data file found, starting with empty data")
    except Exception as e:
        logger.error(f"Error loading user data: {e}")
        users = {}

def save_user_data():
    """Save user data to JSON file"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(USER_DATA_FILE), exist_ok=True)
        
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as file:
            json.dump(users, file, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(users)} user records to file")
    except Exception as e:
        logger.error(f"Error saving user data: {e}")

def get_user_data(user_id):
    """Get user data for a specific user"""
    user_id = str(user_id)  # Convert to string for use as dictionary key
    return users.get(user_id)

def update_user_data(user_id, data):
    """Update user data for a specific user"""
    user_id = str(user_id)  # Convert to string for use as dictionary key
    users[user_id] = data
    # Update last activity timestamp
    users[user_id]["last_activity"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_games_played(user_id):
    """Get the number of games played by user"""
    user_data = get_user_data(str(user_id))
    if user_data:
        return user_data.get("games_played", 0)
    return 0

def get_registration_date(user_id):
    """Get user registration date"""
    user_data = get_user_data(str(user_id))
    if user_data:
        return user_data.get("registration_date", "Unknown")
    return "Unknown"

def get_favorite_game(user_id):
    """Get user's favorite game mode"""
    user_data = get_user_data(str(user_id))
    if user_data:
        return user_data.get("favorite_game")
    return None

def get_all_users():
    """Get a list of all user IDs"""
    return list(users.keys())
