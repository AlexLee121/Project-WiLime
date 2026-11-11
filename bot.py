
import asyncio
import json
import logging
import os
from html import escape
from pathlib import Path

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder


# ---------- Настройка ----------

logging.basicConfig(level=logging.INFO)

# Загружаем переменные окружения из .env
load_dotenv(Path(__file__).with_name(".env"))

# Получаем токен Telegram-бота
TOKEN = os.getenv("BOT_TOKEN")

# Загружаем игровые данные из data.json
DATA_FILE = Path(__file__).with_name("data.json")

def load_data(path: Path) -> dict:
    try:
        with path.open("r", encoding="utf-8") as file:
            games = json.load(file)["games"]
        if not isinstance(games, dict) or not games:
            raise ValueError("games должен быть непустым объектом")
        for game_key, game in games.items():
            if not isinstance(game_key, str) or not game_key or ":" in game_key:
                raise ValueError("неверный ключ игры")
            for field in ("title", "emoji"):
                if not isinstance(game[field], str) or not game[field].strip():
                    raise ValueError(f"{game_key}: неверное поле {field}")
            for category, prefix in (("characters", "char"), ("maps", "map")):
                items = game[category]
                if not isinstance(items, dict):
                    raise ValueError(f"{game_key}: {category} должен быть объектом")
                for key, item in items.items():
                    if not isinstance(key, str) or not key or ":" in key or len(f"{prefix}:{game_key}:{key}".encode()) > 64:
                        raise ValueError(f"{game_key}: неверный или слишком длинный ключ {key}")
                    fields = ("name", "role", "team") if category == "characters" else ("name", "tips")
                    if any(not isinstance(item[field], str) or not item[field].strip() for field in fields):
                        raise ValueError(f"{game_key}/{key}: пустое текстовое поле")
                    lists = ("weapon", "leveling") if category == "characters" else ("steps",)
                    if any(not isinstance(item[field], list) or not item[field] or any(not isinstance(x, str) for x in item[field]) for field in lists):
                        raise ValueError(f"{game_key}/{key}: неверный список")
                    if category == "characters":
                        art = item["artifacts"]
                        if any(not isinstance(art[field], str) or not art[field].strip() for field in ("set", "main_stats", "substats")):
                            raise ValueError(f"{game_key}/{key}: неверные артефакты")
                    if len(item["name"]) > 100:
                        raise ValueError(f"{game_key}/{key}: название кнопки слишком длинное")
            if len(f"chars:{game_key}".encode()) > 64 or len(f"maps:{game_key}".encode()) > 64 or len(game["title"]) > 90:
                raise ValueError(f"{game_key}: ключ или название слишком длинные")
        return games
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f"Ошибка в {path}: {exc}") from exc


DATA = load_data(DATA_FILE)

# Создаём диспетчер бота
dp = Dispatcher()


# ---------- Клавиатуры ----------

def games_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for key, game in DATA.items():
        kb.button(
            text=f"{game['emoji']} {game['title']}",
            callback_data=f"game:{key}"
        )

    kb.adjust(1)
    return kb.as_markup()


def game_menu_kb(game: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    kb.button(
        text="⚔️ Сборка и прокачка персонажей",
        callback_data=f"chars:{game}"
    )

    kb.button(
        text="🗺 Чистка карты",
        callback_data=f"maps:{game}"
    )

    kb.button(
        text="⬅️ К списку игр",
        callback_data="home"
    )

    kb.adjust(1)
    return kb.as_markup()


def chars_kb(game: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for key, ch in DATA[game]["characters"].items():
        kb.button(
            text=ch["name"],
            callback_data=f"char:{game}:{key}"
        )

    kb.button(
        text="⬅️ Назад",
        callback_data=f"game:{game}"
    )

    kb.adjust(2)
    return kb.as_markup()


def maps_kb(game: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    for key, mp in DATA[game]["maps"].items():
        kb.button(
            text=mp["name"],
            callback_data=f"map:{game}:{key}"
        )

    kb.button(
        text="⬅️ Назад",
        callback_data=f"game:{game}"
    )

    kb.adjust(1)
    return kb.as_markup()


def back_kb(callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад",
                    callback_data=callback
                )
            ]
        ]
    )


# ---------- Тексты ----------

def character_text(game: str, key: str) -> str:
    ch = DATA[game]["characters"][key]

    art = ch["artifacts"]

    weapons = "\n".join(
        f"• {escape(w)}" for w in ch["weapon"]
    )

    leveling = "\n".join(
        f"• {escape(s)}" for s in ch["leveling"]
    )

    return (
        f"<b>{escape(ch['name'])}</b> — {escape(ch['role'])}\n\n"
        f"<b>🗡 Оружие</b>\n{weapons}\n\n"
        f"<b>🛡 Артефакты / набор</b>\n{escape(art['set'])}\n\n"
        f"<b>📌 Главные характеристики</b>\n{escape(art['main_stats'])}\n\n"
        f"<b>✨ Желаемые доп. параметры</b>\n{escape(art['substats'])}\n\n"
        f"<b>📈 Прокачка</b>\n{leveling}\n\n"
        f"<b>👥 Команда</b>\n{escape(ch['team'])}"
    )


def map_text(game: str, key: str) -> str:
    mp = DATA[game]["maps"][key]

    steps = "\n".join(
        f"{i}. {escape(s)}"
        for i, s in enumerate(mp["steps"], 1)
    )

    return (
        f"<b>🗺 {escape(mp['name'])} — зачистка карты</b>\n\n"
        f"{steps}\n\n"
        f"💡 <b>Совет:</b> {escape(mp['tips'])}"
    )


# ---------- Команды ----------

@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Привет! Я помогу с билдами, прокачкой персонажей "
        "и зачисткой карты.\n\n"
        "Выбери игру:",
        reply_markup=games_kb()
    )


@dp.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(
        "Команды:\n"
        "/start — выбор игры\n"
        "/help — помощь\n\n"
        "В каждой игре доступны два раздела:\n"
        "⚔️ Сборка и прокачка персонажей\n"
        "🗺 Чистка карты"
    )


# ---------- Обработка кнопок ----------

@dp.callback_query(F.data == "home")
async def home(call: CallbackQuery) -> None:
    await call.message.edit_text(
        "Выбери игру:",
        reply_markup=games_kb()
    )

    await call.answer()


@dp.callback_query(F.data.startswith("game:"))
async def game_menu(call: CallbackQuery) -> None:
    game = call.data.split(":")[1]

    if game not in DATA:
        await call.answer(
            "Игра не найдена",
            show_alert=True
        )
        return

    title = DATA[game]["title"]

    await call.message.edit_text(
        f"<b>{escape(title)}</b>\nВыбери раздел:",
        reply_markup=game_menu_kb(game)
    )

    await call.answer()


@dp.callback_query(F.data.startswith("chars:"))
async def chars_list(call: CallbackQuery) -> None:
    game = call.data.split(":", 1)[1]
    if game not in DATA:
        await call.answer("Игра больше недоступна. Откройте /start", show_alert=True)
        return

    await call.message.edit_text(
        "Выбери персонажа:",
        reply_markup=chars_kb(game)
    )

    await call.answer()


@dp.callback_query(F.data.startswith("char:"))
async def char_card(call: CallbackQuery) -> None:
    parts = call.data.split(":")
    if len(parts) != 3 or parts[1] not in DATA or parts[2] not in DATA[parts[1]]["characters"]:
        await call.answer("Персонаж больше недоступен. Откройте /start", show_alert=True)
        return
    _, game, key = parts
    text = character_text(game, key)
    if len(text) > 4096:
        await call.answer("Карточка слишком длинная. Сообщите администратору.", show_alert=True)
        return
    await call.message.edit_text(
        text,
        reply_markup=back_kb(f"chars:{game}")
    )

    await call.answer()


@dp.callback_query(F.data.startswith("maps:"))
async def maps_list(call: CallbackQuery) -> None:
    game = call.data.split(":", 1)[1]
    if game not in DATA:
        await call.answer("Игра больше недоступна. Откройте /start", show_alert=True)
        return

    await call.message.edit_text(
        "Выбери регион:",
        reply_markup=maps_kb(game)
    )

    await call.answer()


@dp.callback_query(F.data.startswith("map:"))
async def map_card(call: CallbackQuery) -> None:
    parts = call.data.split(":")
    if len(parts) != 3 or parts[1] not in DATA or parts[2] not in DATA[parts[1]]["maps"]:
        await call.answer("Регион больше недоступен. Откройте /start", show_alert=True)
        return
    _, game, key = parts
    text = map_text(game, key)
    if len(text) > 4096:
        await call.answer("Карточка слишком длинная. Сообщите администратору.", show_alert=True)
        return
    await call.message.edit_text(
        text,
        reply_markup=back_kb(f"maps:{game}")
    )

    await call.answer()


# ---------- Запуск бота ----------

async def main() -> None:

    if not TOKEN:
        raise SystemExit(
            "Ошибка: укажите BOT_TOKEN в файле .env"
        )

    proxy = os.getenv("TELEGRAM_PROXY") or None
    session = AiohttpSession(proxy=proxy, timeout=45)
    bot = Bot(
        token=TOKEN,
        session=session,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    logging.info("Запуск бота; прокси %s", "включён" if proxy else "не настроен")
    await dp.start_polling(bot, polling_timeout=25)


if __name__ == "__main__":
    asyncio.run(main())


