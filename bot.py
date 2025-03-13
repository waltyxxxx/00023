#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bot initialization and configuration
"""

import os
import logging
from telegram.request import HTTPXRequest
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                       MessageHandler, filters, ChatMemberHandler)
from handlers import (start, profile_handler, play_handler, 
                     game_selection_handler, cancel_handler,
                     chat_member_handler, instruction_handler,
                     test_api_command)
from user_data import load_user_data

logger = logging.getLogger(__name__)

def create_bot():
    """Create and configure the bot application"""

    # Get bot token from environment variable
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError(
            "No TELEGRAM_BOT_TOKEN found in environment variables")

    # Create the application
    application = Application.builder() \
        .token(token) \
        .request(HTTPXRequest(connect_timeout=30, read_timeout=30)) \
        .build()

    # Load user data
    load_user_data()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("test", test_api_command))

    # Main navigation handlers
    application.add_handler(
        CallbackQueryHandler(profile_handler, pattern="^profile$"))
    application.add_handler(
        CallbackQueryHandler(play_handler, pattern="^play$"))

    # Game handlers
    application.add_handler(
        CallbackQueryHandler(game_selection_handler, pattern="^game_"))

    # API Test handler
    application.add_handler(
        CallbackQueryHandler(test_api_command, pattern="^test_api$"))

    # Instruction handler
    application.add_handler(
        CallbackQueryHandler(instruction_handler, pattern="^instruction$"))

    # Return to main menu
    application.add_handler(
        CallbackQueryHandler(cancel_handler, pattern="^back_to_main$"))

    # Handle other messages
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, cancel_handler))

    # Handle bot being added to or removed from chats
    application.add_handler(
        ChatMemberHandler(chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER))

    return application
