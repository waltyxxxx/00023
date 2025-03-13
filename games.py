#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Game logic for casino games
"""

import random
import logging
import os
from telegram import Update
from telegram.ext import CallbackContext
from crypto_payments import update_user_balance, get_user_balance
from user_data import get_user_data

logger = logging.getLogger(__name__)

# Get channel ID from environment variable
RESULTS_CHANNEL_ID = os.getenv("RESULTS_CHANNEL_ID", "-1002305257035")


async def process_and_send_game_results(update: Update, context: CallbackContext, game_type: str, bet_choice: str, bet_amount: float):
    """
    Process game results and send them to the channel

    Args:
        update: Telegram update object
        context: Context object
        game_type: Type of game (even_odd, higher_lower, bowling)
        bet_choice: User's bet choice
        bet_amount: Bet amount in TON
    """
    user = update.effective_user
    username = user.username or f"user{user.id}"

    if game_type == "bowling":
        message = await update.callback_query.message.reply_dice(emoji="🎳")
        dice_value = message.dice.value
        user_won = (bet_choice == "win" and dice_value >= 4) or (bet_choice == "lose" and dice_value < 4)
        result_text = f"Выпало: {dice_value} очков"

    elif game_type == "even_odd":
        message = await update.callback_query.message.reply_dice(emoji="🎲")
        dice_value = message.dice.value
        is_even = dice_value % 2 == 0
        user_won = (bet_choice == "even" and is_even) or (bet_choice == "odd" and not is_even)
        result_text = "Чет" if is_even else "Нечет"

    else:  # higher_lower
        message = await update.callback_query.message.reply_dice(emoji="🎲")
        dice_value = message.dice.value
        is_higher = dice_value > 3
        user_won = (bet_choice == "higher" and is_higher) or (bet_choice == "lower" and not is_higher)
        result_text = "Больше 3" if is_higher else "Меньше 4"

    # Calculate winnings
    winnings = bet_amount * 1.5 if user_won else -bet_amount

    # Format game type for display
    game_display = {
        "bowling": "🎳 Боулинг",
        "even_odd": "🎲 Чет/Нечет",
        "higher_lower": "📊 Больше/Меньше"
    }.get(game_type, game_type)

    # Format bet choice for display
    bet_display = {
        "win": "Победа",
        "lose": "Поражение",
        "even": "Чет",
        "odd": "Нечет",
        "higher": "Больше",
        "lower": "Меньше"
    }.get(bet_choice, bet_choice)

    # Create result message for channel
    channel_message = (
        f"🎮 Игра: {game_display}\n"
        f"👤 Игрок: @{username}\n"
        f"💰 Ставка: {bet_amount} TON\n"
        f"🎯 Выбор: {bet_display}\n"
        f"🎲 {result_text}\n"
        f"💫 Результат: {'Выигрыш ' + str(winnings) + ' TON' if user_won else 'Проигрыш ' + str(bet_amount) + ' TON'}"
    )

    # Send result to channel
    await context.bot.send_message(
        chat_id=RESULTS_CHANNEL_ID,
        text=channel_message,
        parse_mode="Markdown"
    )

    return {
        "user_won": user_won,
        "winnings": winnings,
        "dice_value": dice_value,
        "result_text": result_text,
        "channel_message": channel_message
    }


async def play_even_odd(update: Update, context: CallbackContext, user_id, bet_choice, bet_amount):
    """
    Play even/odd game
    """
    # First subtract the bet amount from user balance
    current_balance = update_user_balance(user_id, -bet_amount)

    # Send dice animation
    message = await update.callback_query.message.reply_dice(emoji="🎲")
    dice_value = message.dice.value

    # Determine if the result is even or odd
    is_even = dice_value % 2 == 0
    result_text = "Чет" if is_even else "Нечет"
    user_won = (bet_choice == "even" and is_even) or (bet_choice == "odd" and not is_even)

    # Format user-friendly bet choice text
    bet_choice_text = "Чет" if bet_choice == "even" else "Нечет"

    # Calculate winnings for display
    display_winnings = int(bet_amount * 1.5) if user_won else 0

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🎲 Результат броска: {dice_value} ({result_text})\n"
            f"Ваша ставка: {bet_choice_text} ({bet_amount} TON)\n"
            f"Результат: {'🎉 Выигрыш! +' + str(display_winnings) + ' TON' if user_won else '😢 Проигрыш! -' + str(bet_amount) + ' TON'}\n"
            f"Текущий баланс: {get_user_balance(user_id)} TON"
    )

    # Update balance if user won
    winnings = 0
    if user_won:
        winnings = int(bet_amount * 1.5)  # Уменьшен коэффициент с 2 до 1.5
        update_user_balance(user_id, winnings)

    # Create result message for user
    user_message = (
        f"🎲 Результат игры Чет/Нечет:\n\n"
        f"Ваша ставка: {bet_choice_text} - {bet_amount} TON\n"
        f"Выпало: {dice_value} ({result_text})\n\n"
    )

    if user_won:
        user_message += f"🎉 Поздравляем! Вы выиграли {winnings} TON!\n"
    else:
        user_message += f"😢 К сожалению, вы проиграли {bet_amount} TON.\n"

    user_message += f"\nВаш текущий баланс: {get_user_balance(user_id)} TON"

    #Send to channel
    await process_and_send_game_results(update, context, "even_odd", bet_choice, bet_amount)

    # Create channel message
    username = update.callback_query.from_user.username or f"user{user_id}"


    # Create detailed message with statistics
    duplicate_message = (
        f"🎮 Игра: Чет/нечет\n"
        f"🎯 Ваша ставка: {bet_choice_text} ({bet_amount} TON)\n"
        f"🎲 Выпало: {dice_value} ({result_text})\n"
        f"💰 Результат: {'Выигрыш ' + str(winnings) + ' TON' if user_won else 'Проигрыш ' + str(bet_amount) + ' TON'}\n"
        f"💵 Текущий баланс: {get_user_balance(user_id)} TON\n\n"
        f"📊 Статистика игр:\n"
        f"🎮 Всего игр: {get_user_data(user_id).get('games_played', 0) + 1}\n"
        f"🎲 Игр в режиме Чет/нечет: {get_user_data(user_id).get('even_odd_games', 0) + 1}"
    )

    return {
        "message": user_message,
        "duplicate_message": duplicate_message,
        "dice_value": dice_value,
        "user_won": user_won,
        "winnings": winnings if user_won else -bet_amount
    }


async def play_higher_lower(update: Update, context: CallbackContext, user_id, bet_choice, bet_amount):
    """Play higher/lower game"""
    # First subtract the bet amount from user balance
    current_balance = update_user_balance(user_id, -bet_amount)

    # Send dice animation
    message = await update.callback_query.message.reply_dice(emoji="🎲")
    dice_value = message.dice.value

    # Determine if the result is higher than 3 or lower than 4
    is_higher = dice_value > 3
    result_text = "Больше 3" if is_higher else "Меньше 4"
    user_won = (bet_choice == "higher" and is_higher) or (bet_choice == "lower" and not is_higher)

    # Format user-friendly bet choice text
    bet_choice_text = "Больше 3" if bet_choice == "higher" else "Меньше 4"

    # Calculate winnings for display
    display_winnings = int(bet_amount * 1.5) if user_won else 0

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🎲 Результат броска: {dice_value} ({result_text})\n"
             f"Ваша ставка: {bet_choice_text} ({bet_amount} TON)\n"
             f"Результат: {'🎉 Выигрыш! +' + str(display_winnings) + ' TON' if user_won else '😢 Проигрыш! -' + str(bet_amount) + ' TON'}\n"
             f"Текущий баланс: {get_user_balance(user_id)} TON"
    )

    # Update balance if user won
    winnings = 0
    if user_won:
        winnings = int(bet_amount * 1.5)
        update_user_balance(user_id, winnings)

    # Create result message for user
    user_message = (
        f"📊 Результат игры Больше/Меньше:\n\n"
        f"Ваша ставка: {bet_choice_text} - {bet_amount} TON\n"
        f"Выпало: {dice_value} ({result_text})\n\n"
    )

    if user_won:
        user_message += f"🎉 Поздравляем! Вы выиграли {winnings} TON!\n"
    else:
        user_message += f"😢 К сожалению, вы проиграли {bet_amount} TON.\n"

    user_message += f"\nВаш текущий баланс: {get_user_balance(user_id)} TON"

    #Send to channel
    await process_and_send_game_results(update, context, "higher_lower", bet_choice, bet_amount)

    # Create channel message
    username = update.callback_query.from_user.username or f"user{user_id}"


    # Create detailed message with statistics
    duplicate_message = (
        f"🎮 Игра: Больше/меньше\n"
        f"🎯 Ваша ставка: {bet_choice_text} ({bet_amount} TON)\n"
        f"🎲 Выпало: {dice_value} ({result_text})\n"
        f"💰 Результат: {'Выигрыш ' + str(winnings) + ' TON' if user_won else 'Проигрыш ' + str(bet_amount) + ' TON'}\n"
        f"💵 Текущий баланс: {get_user_balance(user_id)} TON\n\n"
        f"📊 Статистика игр:\n"
        f"🎮 Всего игр: {get_user_data(user_id).get('games_played', 0) + 1}\n"
        f"📈 Игр в режиме Больше/меньше: {get_user_data(user_id).get('higher_lower_games', 0) + 1}"
    )

    return {
        "message": user_message,
        "duplicate_message": duplicate_message,
        "dice_value": dice_value,
        "user_won": user_won,
        "winnings": winnings if user_won else -bet_amount
    }