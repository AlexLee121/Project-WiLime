import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

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

    def test_overlong_callback_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.json'
            data = {'games': {'g': {'title': 'Game', 'emoji': '🎮', 'characters': {'a'*65: {}}, 'maps': {}}}}
            path.write_text(json.dumps(data))
            with self.assertRaises(SystemExit):
                bot.load_data(path)


if __name__ == '__main__':
    unittest.main()
