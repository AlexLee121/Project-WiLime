import asyncio
import json
import logging
import os
from html import escape
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

DATA_FILE = Path(__file__).with_name("data.json")
DATA = json.loads(DATA_FILE.read_text(encoding="utf-8"))["games"]

dp = Dispatcher()


def games_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, game in DATA.items():
        kb.button(text=f"{game['emoji']} {game['title']}", callback_data=f"game:{key}")
    kb.adjust(1)
    return kb.as_markup()


def game_menu_kb(game: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="⚔️ Сборка и прокачка персонажей", callback_data=f"chars:{game}")
    kb.button(text="🗺 Чистка карты", callback_data=f"maps:{game}")
    kb.button(text="⬅️ К списку игр", callback_data="home")
    kb.adjust(1)
    return kb.as_markup()


def chars_kb(game: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, ch in DATA[game]["characters"].items():
        kb.button(text=ch["name"], callback_data=f"char:{game}:{key}")
    kb.button(text="⬅️ Назад", callback_data=f"game:{game}")
    kb.adjust(2)
    return kb.as_markup()


def maps_kb(game: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for key, mp in DATA[game]["maps"].items():
        kb.button(text=mp["name"], callback_data=f"map:{game}:{key}")
    kb.button(text="⬅️ Назад", callback_data=f"game:{game}")
    kb.adjust(1)
    return kb.as_markup()


def back_kb(callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data=callback)]]
    )


# ---------- Тексты ----------

def character_text(game: str, key: str) -> str:
    ch = DATA[game]["characters"][key]
    art = ch["artifacts"]
    weapons = "\n".join(f"• {escape(w)}" for w in ch["weapon"])
    leveling = "\n".join(f"• {escape(s)}" for s in ch["leveling"])
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
    steps = "\n".join(f"{i}. {escape(s)}" for i, s in enumerate(mp["steps"], 1))
    return (
        f"<b>🗺 {escape(mp['name'])} — зачистка карты</b>\n\n"
        f"{steps}\n\n"
        f"💡 <b>Совет:</b> {escape(mp['tips'])}"
    )


# ---------- Хендлеры ----------

@dp.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Привет! Я помогу с билдами, прокачкой персонажей и зачисткой карты.\n"
        "Выбери игру:",
        reply_markup=games_kb(),
    )


@dp.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(
        "Команды:\n/start — выбор игры\n/help — помощь\n\n"
        "В каждой игре доступны два раздела: «Сборка и прокачка персонажей» и «Чистка карты».",
    )


@dp.callback_query(F.data == "home")
async def home(call: CallbackQuery) -> None:
    await call.message.edit_text("Выбери игру:", reply_markup=games_kb())
    await call.answer()


@dp.callback_query(F.data.startswith("game:"))
async def game_menu(call: CallbackQuery) -> None:
    game = call.data.split(":")[1]
    if game not in DATA:
        return await call.answer("Игра не найдена", show_alert=True)
    title = DATA[game]["title"]
    await call.message.edit_text(f"<b>{escape(title)}</b>\nВыбери раздел:", reply_markup=game_menu_kb(game))
    await call.answer()


@dp.callback_query(F.data.startswith("chars:"))
async def chars_list(call: CallbackQuery) -> None:
    game = call.data.split(":")[1]
    await call.message.edit_text("Выбери персонажа:", reply_markup=chars_kb(game))
    await call.answer()


@dp.callback_query(F.data.startswith("char:"))
async def char_card(call: CallbackQuery) -> None:
    _, game, key = call.data.split(":")
    await call.message.edit_text(character_text(game, key), reply_markup=back_kb(f"chars:{game}"))
    await call.answer()


@dp.callback_query(F.data.startswith("maps:"))
async def maps_list(call: CallbackQuery) -> None:
    game = call.data.split(":")[1]
    await call.message.edit_text("Выбери регион:", reply_markup=maps_kb(game))
    await call.answer()


@dp.callback_query(F.data.startswith("map:"))
async def map_card(call: CallbackQuery) -> None:
    _, game, key = call.data.split(":")
    await call.message.edit_text(map_text(game, key), reply_markup=back_kb(f"maps:{game}"))
    await call.answer()


async def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise SystemExit("Укажите токен бота в переменной окружения BOT_TOKEN")
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
