#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Main entry point for the Telegram casino bot
"""

import os
import logging
from bot import create_bot

# Set up logging with both console and file handlers (from original code)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        # Create and run the bot
        logger.info("Starting bot initialization...")
        bot = create_bot()
        logger.info("Bot created successfully, starting polling...")
        bot.run_polling(allowed_updates=["message", "callback_query", "my_chat_member"])
        logger.info("Bot started successfully")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        raise