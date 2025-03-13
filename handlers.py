#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Handler functions for the Telegram bot commands and callbacks
"""

import os
import datetime
import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from user_data import (get_user_data, update_user_data, save_user_data, 
                     get_games_played, get_registration_date, get_favorite_game)
from crypto_payments import create_deposit_invoice, test_api_connection, create_fixed_invoice

logger = logging.getLogger(__name__)

# Get channel ID for posting results from environment variables
RESULTS_CHANNEL_ID = os.getenv("-1002305257035")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    try:
        logger.info("Received /start command")

        # Verify update contains necessary data
        if not update.effective_user:
            logger.error("No effective_user in update")
            return

        user = update.effective_user
        user_id = user.id
        logger.info(f"Processing /start command for user {user_id}")

        # Initialize user data if first time
        user_data = get_user_data(user_id)
        if not user_data:
            logger.info(f"Creating new user data for user {user_id}")
            user_data = {
                "user_id": user_id,
                "username": user.username or "Anonymous",
                "registration_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "games_played": 0,
                "favorite_game": None,
                "balance": 0,
                "even_odd_games": 0,
                "higher_lower_games": 0,
                "last_activity": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            update_user_data(user_id, user_data)
            save_user_data()

        # Create welcome keyboard
        keyboard = [
            [
                InlineKeyboardButton("Профиль", callback_data="profile"),
                InlineKeyboardButton("ИГРАТЬ", callback_data="play")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Send welcome message
        await update.message.reply_text(
            "Приветствуем вас в нашем захватывающем казино! 🎰💥 Погрузитесь в мир азарта и удачи прямо сейчас!",
            reply_markup=reply_markup
        )
        logger.info(f"Successfully sent welcome message to user {user_id}")

    except AttributeError as e:
        logger.error(f"AttributeError in start handler: {e}")
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже."
            )
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        if update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Произошла ошибка при запуске бота. Пожалуйста, попробуйте позже."
            )

async def create_payment_url(user_id, bet_amount=4.0):
    """
    Creates a payment URL for CryptoBot.
    Always uses the fixed invoice IV15707697 which shows coin selection first
    and then allows user to enter a custom amount.
    """
    logger.info(f"Creating payment URL for user {user_id}")

    # Always use the fixed invoice that's configured for custom amounts
    fixed_invoice_url = "https://t.me/CryptoBot?start=IV15707697"
    logger.info(f"Created payment URL: {fixed_invoice_url}")
    return fixed_invoice_url

async def send_channel_bet_message(context, user, game_type=None, bet_choice=None, bet_amount=4.0):
    """
    Sends a bet message to the game channel
    """
    logger.info(f"🎮 Sending bet message for user {user.id}")

    try:
        # Create payment URL with arbitrary amount selection
        payment_url = await create_payment_url(user.id, 0.1)

        # Send bet message to channel
        message = await context.bot.send_message(
            chat_id=RESULTS_CHANNEL_ID,
            text=(
                f"🎮 *НОВАЯ СТАВКА* 🔥\n\n"
                f"👤 Игрок: {user.first_name}\n\n"
                f"📝 *В комментарии к платежу укажите:*\n\n"
                f"*Режим и исход:*\n"
                f"• 🎳 Боулинг: `бол - победа` или `бол - поражение`\n"
                f"• 🎲 Чет/Нечет: `чет` или `нечет`\n"
                f"• 📊 Больше/Меньше: `больше` или `меньше`\n\n"
                f"👇 *Введите удобную для вас сумму от 0.1 до 10 TON* при оплате через CryptoBot:"
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Сделать ставку", url=payment_url)],
                [InlineKeyboardButton("📋 Инструкция", callback_data="instruction")]
            ])
        )

        return message
    except Exception as e:
        logger.error(f"Error sending bet message: {e}")
        raise

def get_main_keyboard():
    """Main menu keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("Профиль", callback_data="profile"),
            InlineKeyboardButton("ИГРАТЬ", callback_data="play")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_game_keyboard():
    """Game selection keyboard"""
    keyboard = [
        [InlineKeyboardButton("🎲 Чет/нечет", callback_data="game_even_odd")],
        [InlineKeyboardButton("📊 Больше/меньше", callback_data="game_higher_lower")],
        [InlineKeyboardButton("🎳 Боулинг", callback_data="game_bowling")],
        [InlineKeyboardButton("🧪 Тест API", callback_data="test_api")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle profile button click."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    games_played = get_games_played(user_id)
    registration_date = get_registration_date(user_id)
    favorite_game = get_favorite_game(user_id)

    games_text = f"🎮 Количество сыгранных игр: {games_played}" if games_played > 0 else "🎮 Вы еще не сыграли ни одной игры!"
    favorite_text = f"❤️ Любимый режим: {favorite_game}" if favorite_game else "❤️ У вас еще нет любимого режима игры."

    profile_text = (
        "👤 Ваш профиль:\n\n"
        f"{games_text}\n\n"
        f"📅 Дата регистрации: {registration_date}\n\n"
        f"{favorite_text}"
    )

    await query.edit_message_text(
        text=profile_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
        ])
    )

async def play_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle play button click."""
    try:
        query = update.callback_query
        await query.answer()
    except Exception as e:
        logger.warning(f"Could not answer callback query: {e}")
        pass

    # Use the game channel ID
    channel_id = "-1002305257035"  # Игровой канал
    fixed_channel_url = "https://t.me/test5363627"  # TODO: обновить на реальный URL канала
    channel_url = fixed_channel_url

    user = query.from_user
    payment_url = "https://t.me/CryptoBot?start=IV15707697"  # Используем фиксированный инвойс

    try:
        # Verify bot permissions in the channel
        try:
            bot_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=context.bot.id)
            logger.info(f"Bot permissions in channel {channel_id}: {bot_member.status}")

            if bot_member.status not in ['administrator', 'member']:
                await query.edit_message_text(
                    text="⚠️ Бот не имеет доступа к игровому каналу. Пожалуйста, добавьте бота в канал как администратора и попробуйте снова.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
                    ])
                )
                return
        except Exception as e:
            logger.error(f"Error checking bot permissions: {e}")
            await query.edit_message_text(
                text="⚠️ Бот не имеет доступа к игровому каналу. Пожалуйста, добавьте бота в канал как администратора и попробуйте снова.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
                ])
            )
            return

        # Send bet message to the channel
        message = await context.bot.send_message(
            chat_id=channel_id,
            text=(
                f"🎮 *НОВАЯ СТАВКА* 🔥\n\n"
                f"👤 Игрок: {user.first_name}\n\n"
                f"📝 *В комментарии к платежу укажите:*\n\n"
                f"*Режим и исход:*\n"
                f"• 🎳 Боулинг: `бол - победа` или `бол - поражение`\n"
                f"• 🎲 Чет/Нечет: `чет` или `нечет`\n"
                f"• 📊 Больше/Меньше: `больше` или `меньше`\n\n"
                f"👇 *Введите удобную для вас сумму от 0.1 до 10 TON* при оплате через CryptoBot:"
            ),
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Сделать ставку", url=payment_url)],
                [InlineKeyboardButton("📋 Инструкция", callback_data="instruction")]
            ])
        )
        logger.info(f"Successfully sent bet message to channel {channel_id}")

        # Save bet information in context
        if not context.user_data.get("bets"):
            context.user_data["bets"] = {}

        bet_id = f"{user.id}_{int(datetime.datetime.now().timestamp())}"
        context.user_data["bets"][bet_id] = {
            "game_type": "user_choice",  # User will choose when paying
            "bet_choice": "user_choice",  # User will choose when paying
            "message_id": message.message_id if message else None,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Send success message to user
        await query.edit_message_text(
            text="💎 Хочешь испытать удачу?\n\n💰 Сообщение со ставкой отправлено в канал! Нажмите на кнопку для перехода в канал и оплаты ставки.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎲 Перейти в канал", url=channel_url)],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
            ])
        )
    except Exception as e:
        logger.error(f"Error in play handler when sending to channel {channel_id}: {e}")
        try:
            await query.edit_message_text(
                text="⚠️ Бот не имеет доступа к игровому каналу. Пожалуйста, добавьте бота в канал как администратора и попробуйте снова.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
                ])
            )
        except Exception as edit_error:
            logger.error(f"Failed to send error message to user: {edit_error}")

async def game_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle game selection."""
    query = update.callback_query
    await query.answer()

    logger.info(f"Выбран режим игры: {query.data}")

    parts = query.data.split("_", 1)

    if len(parts) != 2:
        logger.error(f"Неверный формат callback_data: {query.data}")
        return

    prefix, game_type = parts

    user = query.from_user

    await send_channel_bet_message(context, user, None, None)

    await query.edit_message_text(
        text="✅ Ваша ставка принята! Переходите в канал, чтобы сделать ставку.",
        reply_markup=get_main_keyboard()
    )

async def cancel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cancel button click or unknown text messages."""
    if update.callback_query:
        query = update.callback_query
        await query.answer()

        if query.data == "back_to_main":
            await query.edit_message_text(
                text="Приветствуем вас в нашем захватывающем казино! 🎰💥 Погрузитесь в мир азарта и удачи прямо сейчас!",
                reply_markup=get_main_keyboard()
            )
    elif update.message:
        await update.message.reply_text(
            "Пожалуйста, используйте кнопки для взаимодействия с ботом.",
            reply_markup=get_main_keyboard()
        )

async def instruction_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки инструкция"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    instruction_text = "Для продолжения нажмите кнопку 'Сделать ставку' ниже и выберите удобную вам сумму (от 0.1 до 10 TON)"

    logger.warning(f"🔴🔴🔴 СОЗДАНИЕ ССЫЛКИ В ИНСТРУКЦИИ для пользователя {user_id}")
    payment_url = await create_payment_url(user_id, 0.1)

    logger.warning(f"===DEBUG=== Созданный WebApp payment_url: {payment_url}")

    await query.edit_message_text(
        text=instruction_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 Сделать ставку", url=payment_url)],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
        ])
    )

async def test_api_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда для тестирования API CryptoBot"""
    is_callback = False
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        is_callback = True
        message = await query.edit_message_text("🔄 Тестирование подключения к CryptoBot API...")
    else:
        message = await update.message.reply_text("🔄 Тестирование подключения к CryptoBot API...")

    api_result = await test_api_connection()

    logger.info(f"API test result: {api_result}")

    if api_result.get("success"):
        await message.edit_text(
            f"✅ Успешное подключение к CryptoBot API!\n\n"
            f"App ID: {api_result.get('app_id')}\n"
            f"Name: {api_result.get('name')}\n\n"
            f"Создаем тестовый платеж..."
        )

        user_id = update.effective_user.id
        amount = 0.1

        logger.warning(f"🔴🔴🔴 СОЗДАНИЕ ТЕСТОВОГО ИНВОЙСА с произвольной суммой для пользователя {user_id}")
        payment_url = await create_payment_url(user_id, 0.1)

        if isinstance(payment_url, str) and payment_url.startswith("https://"):
            test_success_text = (
                f"✅ Тестовый платежный URL создан успешно!\n\n"
                f"Сумма: {amount} TON\n\n"
                f"Вы можете оплатить его для полного тестирования процесса:"
            )

            test_instructions = "Нажмите кнопку 'Оплатить тестовый счет' для проверки работоспособности"

            if is_callback:
                await message.edit_text(
                    text=test_success_text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Оплатить тестовый счет", url=payment_url)],
                        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
                    ])
                )

                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=test_instructions,
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text(
                    text=test_success_text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Оплатить тестовый счет", url=payment_url)]
                    ])
                )

                await update.message.reply_text(
                    text=test_instructions,
                    parse_mode="Markdown"
                )
        else:
            error_message = payment_url if isinstance(payment_url, str) else "Неизвестная ошибка"
            error_text = f"❌ Ошибка при создании платежного URL:\n\n{error_message}"

            if is_callback:
                await message.edit_text(
                    text=error_text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
                    ])
                )
            else:
                await message.edit_text(error_text)

            logger.error(f"Error creating test payment URL: {error_message}")
    else:
        error_text = f"❌ Ошибка подключения к CryptoBot API:\n\n{api_result.get('message')}"

        if is_callback:
            await message.edit_text(
                text=error_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("◀️ Назад", callback_data="back_to_main")]
                ])
            )
        else:
            await message.edit_text(error_text)

async def chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle bot being added to or removed from a chat"""
    chat_member = update.my_chat_member
    chat_id = chat_member.chat.id

    if chat_member.new_chat_member.status in ["administrator", "member"]:
        logger.info(f"Бот добавлен в чат {chat_id}")

        try:
            # Create payment URL for welcome message
            payment_url = await create_payment_url(context._application.bot.id)

            # Send welcome message with buttons
            welcome_message = (
                "🎰 *Добро пожаловать в Игровой Бот!*\n\n"
                "💎 Сделайте ставку и испытайте свою удачу!\n\n"
                "🎲 *Доступные режимы игры:*\n"
                "• Чет/Нечет\n"
                "• Больше/Меньше\n"
                "• Боулинг\n\n"
                "💡 Выберите режим при оплате ставки, указав комментарий:\n"
                "`Чет и Нечет [Чет/нечет]`\n"
                "`Больше и меньше [Больше/Меньше]`\n"
                "`Боул [Победа/Поражение]`"
            )

            await context.bot.send_message(
                chat_id=chat_id,
                text=welcome_message,
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💰 Сделать ставку", url=payment_url)],
                    [InlineKeyboardButton("📋 Инструкция", callback_data="instruction")]
                ])
            )
            logger.info(f"Отправлено приветственное сообщение в чат {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке приветственного сообщения: {e}")

    elif chat_member.new_chat_member.status in ["left", "kicked"]:
        logger.info(f"Бот удален из чата {chat_id}")

async def process_game_result(update: Update, context: ContextTypes.DEFAULT_TYPE, game_type: str, bet_choice: str, amount: float):
    """
    Process game result and send formatted message to channel
    """
    username = update.effective_user.username or f"user{update.effective_user.id}"

    # Format game type and bet choice for display
    game_display = {
        "bowling": "🎳 Боулинг",
        "even_odd": "🎲 Чет/Нечет",
        "higher_lower": "📊 Больше/Меньше"
    }.get(game_type, game_type)

    bet_display = {
        "win": "Победа",
        "lose": "Поражение",
        "even": "Чет",
        "odd": "Нечет",
        "higher": "Больше",
        "lower": "Меньше"
    }.get(bet_choice, bet_choice)

    # Generate game result
    if game_type == "bowling":
        dice_value = random.randint(1, 6)
        user_won = (bet_choice == "win" and dice_value >= 4) or (bet_choice == "lose" and dice_value < 4)
        result_text = f"Выпало: {dice_value} очков"
    elif game_type == "even_odd":
        dice_value = random.randint(1, 6)
        is_even = dice_value % 2 == 0
        user_won = (bet_choice == "even" and is_even) or (bet_choice == "odd" and not is_even)
        result_text = "Чет" if is_even else "Нечет"
    else:  # higher_lower
        dice_value = random.randint(1, 6)
        is_higher = dice_value > 3
        user_won = (bet_choice == "higher" and is_higher) or (bet_choice == "lower" and not is_higher)
        result_text = "Больше 3" if is_higher else "Меньше 4"

    # Calculate winnings (1.5x for winning)
    winnings = amount * 1.5 if user_won else -amount

    # Format result message
    result_message = (
        f"🎮 Игра: {game_display}\n"
        f"👤 Игрок: @{username}\n"
        f"💰 Ставка: {amount} TON\n"
        f"🎯 Выбор: {bet_display}\n"
        f"🎲 {result_text}\n"
        f"💫 Результат: {'Выигрыш ' + str(winnings) + ' TON' if user_won else 'Проигрыш ' + str(amount) + ' TON'}"
    )

    # Send result to channel
    try:
        await context.bot.send_message(
            chat_id=RESULTS_CHANNEL_ID,
            text=result_message,
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error sending game result to channel: {e}")
        raise

    return {
        "user_won": user_won,
        "winnings": winnings if user_won else -amount,
        "dice_value": dice_value,
        "result_text": result_text
    }
