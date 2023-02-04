# BirthdayBot
## Decription
This bot works with the Discord Python library birthday announcements to all the discord servers it is
connected to.  It allows users to add/update their birthdays and to see what birthdays are coming up.

## bot.py
`bot.py` is the mainframe of BirthdayBot. `bot.py` implements functionalities for adding birthdays, updating birthdays, and sending daily announcements whenever their is a birthday. In order to store the necessary data about the users (their user id, the server id, birthday) and servers, the user of the bot should run `create-tables.sql` to create the tables in the sqlite3 database.

## Setup
1. Clone or download repo.
2. Set up Python virtual enviornment with `python -m venv birthdaybot`
3. Install dependencies with `pip install -r requirements.txt`
4. Download [sqlite3 tools](https://www.sqlite.org/download.html) and run in a terminal:

``` bash
sqlite3 BirthdayBot.db
-> .read create-table.sql
-> .exit
```
5. Create an app on the Discord developer profile, generate a token, and invite the bot to your server using an OAuth2 URL. You need the bot and app command scope and the following permissions:
- Send Messages
- Embeded Links
- Attach Files

You can also just use this URL: `https://discord.com/api/oauth2/authorize?client_id=[CLIENT_ID]&permissions=51200&scope=bot%20applications.commands` but replace `[CLIENT_ID]` with _your_ bot's client ID.

6. Create a .env file with a variable `DISCORD_TOKEN` set to a Discord Bot token (i.e. `DISCORD_TOKEN=[TOKEN]` and `DATABASE=BirthdayBot.db`)

## Running the bot
``` bash
python bot.py
```