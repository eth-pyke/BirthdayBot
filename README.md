# BirthdayBot

## Decription
This bot works with the Discord Python library birthday announcements to all the discord servers it is
connected to.  It allows users to add/update their birthdays and to see what birthdays are coming up.

## bot.py
`bot.py` is the mainframe of BirthdayBot. `bot.py` implements functionalities for adding birthdays, updating birthdays, and sending daily announcements whenever their is a birthday. In order to store the necessary data about the users (their user id, the server id, birthday) and servers, the user of the bot should run `create-tables.sql` to create the tables in the sqlite3 database.

## Usage

Before running the bot, the user must do 2 things; create a .env file with a variable `DISCORD_TOKEN` set to a Discord Bot token (i.e. `DISCORD_TOKEN=[TOKEN]`, and create the database. In order to create the database, run the following commands:

``` bash
sqlite3 BirthdayBot.db
-> .read create-tables.sql
-> .exit
```

Finally, to run the bot, do the following:
```bash
python bot.py
```
