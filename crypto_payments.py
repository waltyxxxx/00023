#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CryptoBot payment integration
"""

import os
import uuid
import json
import logging
import aiohttp
from user_data import get_user_data, update_user_data, save_user_data

logger = logging.getLogger(__name__)

# Get environment variables
CRYPTOBOT_TOKEN = os.getenv("350654:AA4mK8piTvxLsVDBy2Xd2Jt7TrgmePStj2b")
RESULTS_CHANNEL_ID = os.getenv("-1002305257035")

# CryptoBot API URL
CRYPTOBOT_API_URL = "https://pay.crypt.bot/api"

# Track transactions
TRANSACTIONS = {}

async def create_fixed_invoice(coin_id="TON"):
    """
    Создает инвойс для выбора монеты оплаты через API CryptoBot.
    
    Используется только фиксированный инвойс IV15707697 для отображения
    интерфейса выбора валюты и произвольной суммы.

    Args:
        coin_id: Идентификатор монеты (TON, BTC, etc) - не используется
        
    Returns:
        str: URL для выбора криптовалюты и суммы оплаты
    """
    # Просто возвращаем фиксированный инвойс IV15707697, который
    # показывает страницу выбора монеты, а затем страницу ввода суммы
    # точно как на предоставленных пользователем скриншотах
    logger.warning(f"🧿 Используем только фиксированный инвойс IV15707697 для выбора монеты")
    return "https://t.me/CryptoBot?start=IV15707697"

#фикс 1

async def create_deposit_invoice(user_id, amount):
    """
    Create a deposit invoice using CryptoBot API with dynamic amount and user-specific details.
    
    Args:
        user_id: Telegram user ID
        amount: Amount to deposit in TON
        
    Returns:
        str: Payment URL for the invoice
    """
    logger.info(f"Создание динамического счета для пользователя {user_id} на сумму {amount} TON")
    
    # Проверяем наличие токена CryptoBot
    if not CRYPTOBOT_TOKEN:
        logger.error("CryptoBot token not found.")
        return None
    
    # Формируем URL для создания инвойса через API CryptoBot
    url = f"{CRYPTOBOT_API_URL}/createInvoice"
    
    # Подготавливаем данные для запроса
    payload = {
        "asset": "TON",  # Используем TON как валюту
        "amount": str(amount),  # Сумма в TON
        "description": f"Deposit for user {user_id}",  # Описание счета
        "hidden_message": f"user_id:{user_id}",  # Скрытое сообщение для идентификации пользователя
        "allow_anonymous": False,  # Запрещаем анонимные платежи
        "allow_comments": True  # Разрешаем комментарии к платежу
    }
    
    # Заголовки запроса
    headers = {
        "Crypto-Pay-API-Token": CRYPTOBOT_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        # Отправляем запрос на создание инвойса
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                result = await response.json()
                
                # Проверяем успешность запроса
                if response.status == 200 and result.get("ok"):
                    # Возвращаем URL для оплаты
                    payment_url = result.get("result", {}).get("pay_url")
                    logger.info(f"Создан динамический счет для пользователя {user_id}: {payment_url}")
                    return payment_url
                else:
                    # Логируем ошибку, если запрос не удался
                    error_msg = result.get("error", {}).get("message", "Unknown error")
                    logger.error(f"Ошибка при создании инвойса: {error_msg}")
                    return None
    except Exception as e:
        # Логируем исключение, если что-то пошло не так
        logger.error(f"Исключение при создании инвойса: {e}")
        return None

async def create_withdrawal(user_id, amount, wallet_address, use_cryptobot_user=False, cryptobot_user_id=None):
    """
    Create a withdrawal request using CryptoBot API
    
    Args:
        user_id: Telegram user ID
        amount: Amount to withdraw in TON
        wallet_address: External TON wallet address, or "cryptobot" for direct CryptoBot transfer
        use_cryptobot_user: Whether to use CryptoBot user ID for direct transfer
        cryptobot_user_id: CryptoBot user ID for direct transfer
    """
    logger.info(f"Создание запроса на вывод для пользователя {user_id} на сумму {amount} TON")
    
    # Проверка достаточности средств
    current_balance = get_user_balance(user_id)
    if current_balance < amount:
        return {
            "success": False,
            "message": f"Недостаточно средств. Ваш баланс: {current_balance} TON"
        }
    
    # Проверяем наличие токена CryptoBot
    if not CRYPTOBOT_TOKEN:
        logger.error("CryptoBot token not found.")
        return {
            "success": False,
            "message": "Ошибка: Токен CryptoBot недоступен. Обратитесь к администратору."
        }
    
    # Генерируем уникальный ID транзакции
    transaction_id = str(uuid.uuid4())
    
    # Формируем URL запроса
    url = f"{CRYPTOBOT_API_URL}/transfer"
    
    # Комиссия на вывод (можно настраивать)
    # При выводе на CryptoBot нет комиссии
    fee = 0 if use_cryptobot_user else 0.1  # TON
    net_amount = amount - fee
    
    # Готовим данные для запроса
    if use_cryptobot_user and cryptobot_user_id:
        # Прямой перевод другому пользователю CryptoBot
        payload = {
            "user_id": str(cryptobot_user_id),
            "asset": "TON",
            "amount": str(net_amount),
            "spend_id": f"withdrawal_{user_id}_{transaction_id}",
            "comment": f"Вывод средств из Casino Bot: {net_amount} TON",
            "disable_send_notification": "false"
        }
    else:
        # Перевод на внешний кошелек
        payload = {
            "asset": "TON",
            "amount": str(net_amount),
            "wallet_address": wallet_address,
            "comment": f"Withdrawal for user {user_id}"
        }
    
    headers = {
        "Crypto-Pay-API-Token": CRYPTOBOT_TOKEN,
        "Content-Type": "application/json"
    }
    
    # Сохраняем информацию о транзакции
    TRANSACTIONS[transaction_id] = {
        "user_id": user_id,
        "type": "withdrawal",
        "amount": amount,
        "net_amount": net_amount,
        "fee": fee,
        "wallet": wallet_address if not use_cryptobot_user else f"CryptoBot: {cryptobot_user_id}",
        "status": "pending"
    }
    
    try:
        # Списываем средства заранее
        update_user_balance(user_id, -amount)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                result = await response.json()
                
                if response.status == 200 and result.get("ok"):
                    transfer_data = result.get("result", {})
                    transfer_id = transfer_data.get("transfer_id")
                    
                    # Обновляем информацию о транзакции
                    TRANSACTIONS[transaction_id]["transfer_id"] = transfer_id
                    TRANSACTIONS[transaction_id]["status"] = "completed"
                    
                    logger.info(f"Успешно создан вывод #{transfer_id} для пользователя {user_id}")
                    
                    if use_cryptobot_user:
                        return {
                            "success": True,
                            "message": f"{net_amount} TON успешно отправлены на ваш CryptoBot аккаунт.",
                            "transaction_id": transaction_id
                        }
                    else:
                        return {
                            "success": True,
                            "message": f"{net_amount} TON успешно отправлены на кошелек {wallet_address}.\nКомиссия: {fee} TON",
                            "transaction_id": transaction_id
                        }
                else:
                    error_msg = result.get("error", {}).get("message", "Unknown error")
                    logger.error(f"CryptoBot API error: {error_msg}")
                    
                    # Возвращаем средства пользователю
                    update_user_balance(user_id, amount)
                    
                    # Обновляем статус транзакции
                    TRANSACTIONS[transaction_id]["status"] = "failed"
                    TRANSACTIONS[transaction_id]["error"] = error_msg
                    
                    return {
                        "success": False,
                        "message": f"Ошибка при создании вывода: {error_msg}"
                    }
    except Exception as e:
        logger.error(f"Exception during withdrawal creation: {e}")
        
        # Возвращаем средства пользователю
        update_user_balance(user_id, amount)
        
        # Обновляем статус транзакции
        TRANSACTIONS[transaction_id]["status"] = "failed"
        TRANSACTIONS[transaction_id]["error"] = str(e)
        
        return {
            "success": False,
            "message": f"Ошибка соединения с сервисом: {str(e)}"
        }

async def check_transaction_status(transaction_id):
    """Check status of a transaction"""
    if transaction_id in TRANSACTIONS:
        return TRANSACTIONS[transaction_id]
    return None

async def get_transaction_history(user_id, limit=10):
    """Get transaction history for a user"""
    user_transactions = []
    
    for tx_id, tx_data in TRANSACTIONS.items():
        if tx_data.get("user_id") == user_id:
            tx_info = tx_data.copy()
            tx_info["transaction_id"] = tx_id
            user_transactions.append(tx_info)
    
    # Sort by timestamp if available, otherwise just return the most recent (limited)
    return user_transactions[:limit]

def get_user_balance(user_id):
    """Get user balance from user data"""
    user_data = get_user_data(user_id)
    if user_data:
        return user_data.get("balance", 0)
    return 0

def update_user_balance(user_id, amount_change):
    """Update user balance by adding/subtracting amount"""
    user_data = get_user_data(user_id)
    if user_data:
        # Ensure we don't go below zero
        user_data["balance"] = max(0, user_data.get("balance", 0) + amount_change)
        update_user_data(user_id, user_data)
        save_user_data()
        
        # Log the balance change
        if amount_change > 0:
            logger.info(f"Пополнение баланса пользователя {user_id} на {amount_change} TON. Новый баланс: {user_data['balance']} TON")
        else:
            logger.info(f"Списание с баланса пользователя {user_id} на {abs(amount_change)} TON. Новый баланс: {user_data['balance']} TON")
            
        return user_data["balance"]
    return 0

async def process_payment_update(update_data):
    """Process payment update from CryptoBot"""
    try:
        if update_data.get("update_type") == "invoice_paid":
            invoice = update_data.get("payload", {})
            hidden_message = invoice.get("hidden_message", "")
            payment_comment = invoice.get("comment", "")

            # Log payment comment for debugging
            logger.info(f"Received payment with comment: {payment_comment}")

            user_id = None
            transaction_id = None

            # Determine game type and user choice from comment
            game_type = None
            bet_choice = None

            # Process comment to determine game mode and choice
            if payment_comment:
                payment_comment = payment_comment.lower().strip()

                # Check for Чет/Нечет
                if "чет и нечет" in payment_comment:
                    game_type = "even_odd"
                    if "[чет]" in payment_comment:
                        bet_choice = "even"
                    elif "[нечет]" in payment_comment:
                        bet_choice = "odd"

                # Check for Больше/Меньше
                elif "больше и меньше" in payment_comment:
                    game_type = "higher_lower"
                    if "[больше]" in payment_comment:
                        bet_choice = "higher"
                    elif "[меньше]" in payment_comment:
                        bet_choice = "lower"

                # Check for Боулинг
                elif "боул" in payment_comment:
                    game_type = "bowling"
                    if "[победа]" in payment_comment:
                        bet_choice = "win"
                    elif "[поражение]" in payment_comment:
                        bet_choice = "lose"

            # Log determined game type and choice
            logger.info(f"Determined game type: {game_type}, bet choice: {bet_choice}")

            # Extract user_id from hidden_message
            if "user_id:" in hidden_message:
                parts = hidden_message.split(",")
                for part in parts:
                    if part.startswith("user_id:"):
                        try:
                            user_id = int(part.replace("user_id:", "").strip())
                        except ValueError:
                            logger.error(f"Invalid user_id format in hidden message: {part}")
                    elif part.startswith("txid:"):
                        transaction_id = part.replace("txid:", "").strip()

            if user_id and game_type and bet_choice:
                amount = float(invoice.get("amount", 0))
                asset = invoice.get("asset", "TON")
                invoice_id = invoice.get("invoice_id", "unknown")

                # Update user balance
                update_user_balance(user_id, amount)
                logger.info(f"Updated balance for user {user_id} with +{amount} {asset}")

                # Process game results
                try:
                    from games import process_and_send_game_results
                    game_result = await process_and_send_game_results(
                        update=update_data.get("update"),
                        context=update_data.get("context"),
                        game_type=game_type,
                        bet_choice=bet_choice,
                        bet_amount=amount
                    )

                    # Update user balance with winnings/losses
                    if game_result.get("user_won"):
                        winnings = game_result.get("winnings", 0)
                        update_user_balance(user_id, winnings)
                        logger.info(f"Updated user balance after game: {winnings} TON")

                except Exception as e:
                    logger.error(f"Error processing game results: {e}")

                return {
                    "success": True,
                    "user_id": user_id,
                    "amount": amount,
                    "asset": asset,
                    "game_type": game_type,
                    "bet_choice": bet_choice,
                    "transaction_id": transaction_id
                }

            else:
                missing = []
                if not user_id:
                    missing.append("user_id")
                if not game_type:
                    missing.append("game_type")
                if not bet_choice:
                    missing.append("bet_choice")

                logger.warning(f"Invalid payment data. Missing: {', '.join(missing)}")
                return {
                    "success": False,
                    "message": f"Invalid payment data. Missing: {', '.join(missing)}"
                }

        else:
            logger.info(f"Non-invoice update received: {update_data.get('update_type')}")
            return {
                "success": False,
                "message": "Not an invoice_paid update"
            }

    except Exception as e:
        logger.error(f"Error processing payment update: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

async def check_payment_status(invoice_id):
    """Check status of a payment by invoice ID"""
    if not CRYPTOBOT_TOKEN:
        logger.error("CryptoBot token not found.")
        return {
            "success": False,
            "message": "CryptoBot token not available"
        }
    
    url = f"{CRYPTOBOT_API_URL}/getInvoices"
    params = {"invoice_ids": [invoice_id]}
    
    headers = {
        "Crypto-Pay-API-Token": CRYPTOBOT_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                result = await response.json()
                
                if response.status == 200 and result.get("ok"):
                    invoices = result.get("result", {}).get("items", [])
                    if invoices:
                        invoice = invoices[0]
                        return {
                            "success": True,
                            "status": invoice.get("status"),
                            "paid": invoice.get("paid"),
                            "amount": invoice.get("amount"),
                            "asset": invoice.get("asset")
                        }
                    else:
                        return {
                            "success": False,
                            "message": "Invoice not found"
                        }
                else:
                    error_msg = result.get("error", {}).get("message", "Unknown error")
                    return {
                        "success": False,
                        "message": f"API error: {error_msg}"
                    }
    except Exception as e:
        logger.error(f"Error checking payment status: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }

async def test_api_connection():
    """Test connection to CryptoBot API"""
    if not CRYPTOBOT_TOKEN:
        logger.error("CryptoBot token not found.")
        return {
            "success": False,
            "message": "CryptoBot token not available"
        }
    
    url = f"{CRYPTOBOT_API_URL}/getMe"
    
    headers = {
        "Crypto-Pay-API-Token": CRYPTOBOT_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                result = await response.json()
                
                if response.status == 200 and result.get("ok"):
                    app_info = result.get("result", {})
                    return {
                        "success": True,
                        "app_id": app_info.get("app_id"),
                        "name": app_info.get("name"),
                        "payment_processing_bot_username": app_info.get("payment_processing_bot_username")
                    }
                else:
                    error_msg = result.get("error", {}).get("message", "Unknown error")
                    error_code = result.get("error", {}).get("code", None)
                    return {
                        "success": False,
                        "message": error_msg,
                        "code": error_code
                    }
    except Exception as e:
        logger.error(f"Error testing API connection: {e}")
        return {
            "success": False,
            "message": f"Connection error: {str(e)}"
        }

def validate_ton_wallet(address):
    """Validate TON wallet address format"""
    # Базовая валидация TON-адреса
    if not address:
        return False
    
    # TON addresses are typically base64 and start with "EQ" or "UQ"
    if address.startswith("EQ") or address.startswith("UQ"):
        # Check min length
        if len(address) >= 48:
            return True
    
    return False

async def create_invoice_for_transfer(user_id, amount, cryptobot_user_id):
    """
    Create an invoice request for transfer from user's CryptoBot account
    
    Args:
        user_id: Telegram user ID
        amount: Amount to request in TON
        cryptobot_user_id: CryptoBot user ID to request from
    """
    # Просто возвращаем фиксированный инвойс, как и для обычных платежей
    return "https://t.me/CryptoBot?start=IV15707697"
