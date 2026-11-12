# Game Wiki Telegram Bot

Games: Genshin Impact, Honkai: Star Rail, and Zenless Zone Zero.
Each game has two sections: character builds and progression, and map exploration and completion.

## Running on Windows with VS Code

1. Install Python and open the project folder in VS Code: **File → Open Folder**.
2. Open the terminal (**Terminal → New Terminal**) and select PowerShell. If the terminal is in a different directory, navigate to the project folder, for example: `cd "C:\Users\YourName\Project-WiLime"`.
3. Install the dependencies and check that Python 3.10 or newer is installed:

   ```powershell
   py --version
   py -m pip install -r requirements.txt
   ```

4. Create a bot using @BotFather. In the same terminal, set your token and start the bot:

   ```powershell
   $env:BOT_TOKEN="your_token"
   py bot.py
   ```

   Keep the terminal open while the bot is running. After stopping it, run the commands in step 4 again. If `py` is not recognised, try `python --version` and use `python` instead of `py` in both commands. Press Ctrl+C to stop the bot.

For Linux/macOS: run `python3 -m pip install -r requirements.txt`, then `BOT_TOKEN='your_token' python3 bot.py`.

## Adding a Game, Character, or Region

All content is stored in `data.json`, so you do not need to modify the Python code:

- **New character:** add an entry under `characters` for the appropriate game.
- **New region:** add an entry under `maps`.
- **New game:** add a key under `games` with the fields `title`, `emoji`, `characters`, and `maps`.

## Connecting to Telegram

The bot requires access to `api.telegram.org` from the computer or server where it runs. If a direct connection is unavailable, you can run the bot on a server that can reach Telegram or configure your own HTTP/SOCKS5 proxy in a `.env` file next to `bot.py`:

```dotenv
BOT_TOKEN=your_token
TELEGRAM_PROXY=socks5://user:password@proxy.example:1080
```

Replace the sample proxy address and credentials with the actual details provided by your proxy provider. If the direct connection works, you can omit `TELEGRAM_PROXY`. Never publish your `.env` file.

The bot automatically retries connections after network errors, but it still requires a reachable Telegram server or proxy. These settings do not resolve any restrictions that users themselves may face when accessing Telegram. Normally, run only one instance of the bot per token.

The game data contains draft recommendations. Check character builds against the current game version and reliable sources.

## Tests

```bash
python -m unittest discover -s tests -v
```
