#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Constants and configuration values
"""

import os

# Channel ID for posting game results (set from environment or leave as None)
RESULTS_CHANNEL_ID = os.getenv("-1002305257035")

# Default deposit amounts
DEFAULT_DEPOSIT_AMOUNTS = [50, 100, 200, 500]

# Game settings
DEFAULT_BET_AMOUNT = 100
BET_AMOUNTS = [50, 100, 200]

# Even/Odd game multiplier (1.5x means you get 1.5 times your bet if you win)
EVEN_ODD_MULTIPLIER = 1.5

# Higher/Lower game multiplier
HIGHER_LOWER_MULTIPLIER = 1.5

# Number to compare in Higher/Lower game
HIGHER_LOWER_THRESHOLD = 3  # Higher than 3, Lower than 4
