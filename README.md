# Telegram-бот по играм

Игры: Genshin Impact, Honkai: Star Rail, Zenless Zone Zero.
В каждой игре два раздела: сборка и прокачка персонажей, чистка карты.

## Запуск

1. Создайте бота у @BotFather и получите токен.
2. Установите зависимости: `pip install -r requirements.txt`
3. Задайте токен и запустите:
   - Linux/macOS: `BOT_TOKEN=ваш_токен python bot.py`
   - Windows (PowerShell): `$env:BOT_TOKEN="ваш_токен"; python bot.py`

## Как добавить игру, персонажа или регион

Всё содержимое лежит в `data.json`. Код менять не нужно:
- новый персонаж — добавьте объект в `characters` нужной игры;
- новый регион — добавьте объект в `maps`;
- новая игра — добавьте ключ в `games` с полями `title`, `emoji`, `characters`, `maps`.

## Важно

Данные в `data.json` — стартовый набор. Билды меняются с патчами, поэтому
перед публикацией сверьте их с актуальными источниками (Prydwen, Hoyolab, Game8).
