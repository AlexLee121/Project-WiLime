import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from aiogram.exceptions import TelegramNetworkError, TelegramUnauthorizedError, TelegramBadRequest
from aiogram.methods import GetMe, EditMessageText

import bot


class BotTests(unittest.TestCase):
    def test_data_and_keyboard(self):
        self.assertTrue(bot.DATA)
        for game, data in bot.DATA.items():
            bot.game_menu_kb(game)
            bot.chars_kb(game)
            bot.maps_kb(game)
            for key in data['characters']:
                self.assertLessEqual(len(bot.character_text(game, key)), 4096)
            for key in data['maps']:
                self.assertLessEqual(len(bot.map_text(game, key)), 4096)

    def test_invalid_file_reports_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.json'
            path.write_text(json.dumps({'games': {'broken': {}}}))
            with self.assertRaisesRegex(SystemExit, 'Ошибка в'):
                bot.load_data(path)

    def test_old_and_malformed_buttons(self):
        async def run():
            for handler, data in [(bot.char_card, 'char:genshin:missing'),
                                  (bot.char_card, 'char:bad'),
                                  (bot.map_card, 'map:missing:region'),
                                  (bot.chars_list, 'chars:missing'),
                                  (bot.maps_list, 'maps:missing')]:
                call = SimpleNamespace(data=data, answer=AsyncMock(), message=SimpleNamespace(edit_text=AsyncMock()))
                await handler(call)
                call.answer.assert_awaited_once()
                call.message.edit_text.assert_not_awaited()
        asyncio.run(run())

    def test_startup_retries_network_failures(self):
        async def run():
            client = SimpleNamespace(me=AsyncMock(side_effect=[
                TelegramNetworkError(method=GetMe(), message="timeout"),
                TelegramNetworkError(method=GetMe(), message="timeout"),
                object(),
            ]))
            with patch("bot.asyncio.sleep", new_callable=AsyncMock) as sleep:
                await bot.wait_for_telegram(client)
            self.assertEqual(client.me.await_count, 3)
            self.assertEqual([call.args[0] for call in sleep.await_args_list], [1, 2])
        asyncio.run(run())

    def test_invalid_token_is_not_retried(self):
        async def run():
            client = SimpleNamespace(me=AsyncMock(side_effect=TelegramUnauthorizedError(method=GetMe(), message="Unauthorized")))
            with patch("bot.asyncio.sleep", new_callable=AsyncMock) as sleep:
                with self.assertRaises(TelegramUnauthorizedError):
                    await bot.wait_for_telegram(client)
                sleep.assert_not_awaited()
        asyncio.run(run())

    def test_repeated_click_and_other_bad_requests(self):
        async def run():
            for description, suppressed in [("message is not modified", True), ("message to edit not found", False)]:
                error = TelegramBadRequest(method=EditMessageText(text="test"), message=description)
                call = SimpleNamespace(answer=AsyncMock(), message=SimpleNamespace(edit_text=AsyncMock(side_effect=error)))
                if suppressed:
                    await bot.home(call)
                    call.answer.assert_awaited_once()
                else:
                    with self.assertRaises(TelegramBadRequest):
                        await bot.home(call)
                    call.answer.assert_not_awaited()
        asyncio.run(run())

    def test_overlong_callback_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.json'
            data = {'games': {'g': {'title': 'Game', 'emoji': '🎮', 'characters': {'a'*65: {}}, 'maps': {}}}}
            path.write_text(json.dumps(data))
            with self.assertRaises(SystemExit):
                bot.load_data(path)


if __name__ == '__main__':
    unittest.main()

