################################################################################################
# Birthday Bot
# bot.py
#
# Oringial Author: Ethan Pyke
#
# This is a Discord bot meant to run on a container that keeps track of users
# birthdays and announces when it is their birthday.
################################################################################################

import os
import sqlite3
import re
import logging
from signal import signal, SIGINT
import asyncio

import discord
from typing import Optional
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands, tasks
import datetime
from datetime import datetime, time
import dateutil
from dateutil.parser import parse

startUpTime = datetime.now().time()
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE = os.getenv('DATABASE')

MONTHS = {1:31, 2:29, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 
            12:31}
MONTH_NAMES =['January', 'February', 'March', 'April', 'May', 'June', 'July', 
                'August', 'September', 'October', 'November', 'December']

TEST_GUILD = discord.Object(id=721192014192050216)

print("\
################################################################################################\n\
BirthdayBot V2.0\n\
################################################################################################\
\
")

logging.basicConfig(level=logging.DEBUG)

# Connect db
# TODO add database check
connection = sqlite3.connect(DATABASE)#, detect_types=sqlite3.PARSE_DECLTYPES)

def getAnnounceTime():
    cursor = connection.cursor()
    cursor.execute(f"SELECT announceTime, serverID, channelID FROM Servers WHERE announceTime NOT NULL")
    rows = cursor.fetchall()
    return[(time.fromisoformat(x[0]), x[1], x[2]) for x in rows]

announceTime = getAnnounceTime()

def announceOnlyTime(): return [x[0] for x in announceTime]

if not announceTime:
    announceTime = [(datetime.now().time(), 0)]

class BirthdayBot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=TEST_GUILD)
        await self.tree.sync()
        self.birthday_message.start()

    @tasks.loop(time=announceOnlyTime())
    async def birthday_message(self):
        checkTime = self.birthday_message._last_iteration.time()
        logging.info(f"Checking for birthdays for servers set to {checkTime}")
        
        cursor = connection.cursor()

        channels = [x for x in announceTime if x[0] == checkTime]

        for channel in channels:
            message_channel = self.get_channel(channel[2])
            if not message_channel: raise TypeError("message_channel is None")

            currdate = datetime.now().date()
            mm = currdate.month
            dd = currdate.day
            yyyy = currdate.year
            if mm < 10:
                mm = f'0{mm}'
            if dd < 10:
                dd = f'0{dd}'
            cursor.execute(f"SELECT * FROM Birthdays WHERE bday LIKE '%-{mm}-{dd}' AND guildID={message_channel.guild.id}")
            rows = cursor.fetchall()

            if rows:
                embed = discord.Embed(
                title=":birthday:❗__Birthday Announcement__❗:birthday:",
                description=f"\nSomeone's Birthday is Today!\n",
                color=discord.Color.red())
                file = discord.File("img/birthdaybot.png", filename="birthdaybot.png")
                embed.set_thumbnail(url="attachment://birthdaybot.png")

                # Make birthday list
                val = ""
                for row in rows:
                    age = yyyy - int(row[3].split("-")[0])
                    val += f"  - <@!{row[0]}> is turning {age} years old! :confetti_ball:\n"
                val +="\nMake sure to wish them a Happy Birthday!"
                
                if (len(rows) == 1):
                    embed.add_field(name=f"**There is 1 birthday today:**", value=f"{val}")
                else:
                    embed.add_field(name=f"**There are {len(rows)} birthdays today:**", value=f"{val}")

                # Add footer
                embed.set_footer(text="If you want everyone to be notified of your birthday, use /add under BirthdayBot")
                await message_channel.send(f"@everyone! BirthdayBot here with a Special **Birthday Announcement**!", file=file, embed=embed)

    @birthday_message.before_loop
    async def before(self):
        print("Waiting for bot to be ready...")
        await self.wait_until_ready()
        print("Finished waiting, starting loop...")

    @birthday_message.after_loop
    async def after(self):
        print("Loop cancelled.")      

intents = discord.Intents.default()
bot = BirthdayBot(intents=intents)

##############################
# Private Functions          #
##############################

def checkValidDate(date: str):
    if not(date and re.search(r"^\d{4}-\d{2}-\d{2}$", date)):
        return False

    date = date.split('-')
    year = int(date[0])
    month = int(date[1])
    date = int(date[2])
    curryear = datetime.now().date().year

    if ((year < curryear - 100 or year > curryear) or (month < 1 or month > 12) or (date < 1 or date > MONTHS[month])):
        return False

    return True

def checkSetup(interaction: discord.Interaction):
    cursor = connection.cursor()
    cursor.execute(f"SELECT * FROM Servers WHERE serverID={interaction.guild_id} AND channelID NOT NULL")
    row = cursor.fetchone()
    if (not row):
        #await interaction.response.send_message("Please set the channel where birthdays will be announced.", ephemeral=True)
        return False
    return True

async def updateBirthday(cursor, interaction: discord.Interaction, birthdate : str, user):
    cursor.execute(f"SELECT * FROM Birthdays WHERE userID={user.id} AND guildID={interaction.guild_id}")
    row = cursor.fetchone()
    if row:
        #update
        cursor.execute(f"UPDATE Birthdays SET bday = '{birthdate}' WHERE USERID = {user.id} AND guildID={interaction.guild.id}")
        connection.commit()
        await interaction.response.send_message('Birthday updated successfully.', ephemeral=True)
    
    else:
        #insert
        cursor.execute(f"INSERT INTO Birthdays VALUES ({user.id}, {interaction.guild_id}, '{user.name}', '{birthdate}')")
        connection.commit()
        await interaction.response.send_message('Birthday added successfully', ephemeral=True)

async def addServerToDB(guild: discord.Guild):
    logging.info("Adding " + guild.name + "(" + str(guild.id) + ") to DB")
    cursor = connection.cursor()
    cursor.execute(f"INSERT INTO Servers VALUES({guild.id},'{guild.name}', NULL, NULL)")
    connection.commit()

##############################
# Discord Commands and Calls #
##############################
@bot.event
async def on_ready():
    print(bot.guilds)
    for g in bot.guilds:
        print(f'{bot.user.name} has connected to {g.name}!\n')

    cursor = connection.cursor()
    cursor.row_factory = lambda cursor, row: row[0]
    cursor.execute(f"SELECT serverID FROM Servers")
    serversInDB = cursor.fetchall()
    for i in bot.guilds:
        if i.id not in serversInDB:
            logging.warning("Bot connected to " + i.name + " and was not in DB." +\
            " Was the DB deleted?")
            await addServerToDB(i)

@bot.event
async def on_disconnect():
    print(f'{bot.user.name} has disconnected.')

@bot.event
async def on_resumed():
    print(f'{bot.user.name} has reconnected.')

@bot.event
async def on_guild_join(guild):
    addServerToDB(guild)
    # TODO add message about setup

@bot.event
async def on_guild_remove(guild):
    print(guild.id)
    print(guild.name)
    cursor = connection.cursor()
    cursor.execute(f"DELETE FROM Servers WHERE serverID = {guild.id}")
    cursor.execute(f"DELETE FROM Birthdays WHERE guildID = {guild.id}")
    connection.commit()

# /add
@bot.tree.command(name="add", description="Add birthday with date in YYYY-MM-DD format.")
@app_commands.describe(birthdate="Birthdate in YYYY-MM-DD format", user="Who's Birthdate (Default: you)")
async def add(interaction: discord.Interaction, birthdate: str, user: Optional[discord.Member] = None):
    
    if user == None or user == interaction.user: user = interaction.user
    elif not interaction.permissions.manage_guild:
        await interaction.response.send_message('You do not have permission ' + 
        'to change another user\'s birthdate. You must have the Manage Server permission.', ephemeral=True)

        return

    cursor = connection.cursor()

    if not checkSetup(interaction):
        await interaction.response.send_message('Please finish setup.', ephemeral=True)
    elif checkValidDate(birthdate):
        await updateBirthday(cursor, interaction, birthdate, user)
    else:
        await interaction.response.send_message('Either you did not provide a birthday or the date was not formatted like YYYY-MM-DD.', ephemeral=True)

# /update
@bot.tree.command(name="update", description="Update a user's birthday.")
@app_commands.describe(birthdate="Birthdate in YYYY-MM-DD format", user="Who's Birthdate (Default: you)")
async def update(interaction: discord.Interaction, birthdate: str, user: Optional[discord.Member] = None):
    
    if user == None or user == interaction.user: user = interaction.user
    elif not interaction.permissions.manage_guild:
        await interaction.response.send_message('You do not have permission ' + 
        'to change another user\'s birthdate. You must have the Manage Server permission.', ephemeral=True)

        return

    cursor = connection.cursor()

    if not checkSetup(interaction):
        await interaction.response.send_message('Please finish setup.', ephemeral=True)
    elif checkValidDate(birthdate):
        await updateBirthday(cursor, interaction, birthdate, user)
    else:
        await interaction.response.send_message('Either you did not provide a birthday or the date was not formatted like YYYY-MM-DD.', ephemeral=True)

# /month
@bot.tree.command(name="month", description="Lists who has birthdays this month.")
@app_commands.describe(input="Month number (1-12) (optional)")
async def month(interaction: discord.Interaction, 
    input: Optional[app_commands.Range[int, 0, 2399]] = None):
    
    cursor = connection.cursor()

    currmonth = 0
    curr_month_name = ""
    
    # Checks if input is valid. Probably can get rid of this, 
    # but keeping just incase
    if (input):
        if (int(input) > 0 and int(input) <= 12):
            curr_month_name = MONTH_NAMES[int(input) - 1]
            if int(input) < 10:
                currmonth = f'0{input}'
            else:
                currmonth = input
        else:
            await interaction.response.send_message(
                "Please enter a valid number from 1-12.", ephemeral=True)
            return
    else:
        currmonth = datetime.now().date().month
        curr_month_name = MONTH_NAMES[currmonth - 1]
        if currmonth < 10:
            currmonth = f'0{currmonth}'
    
    # Finds birthdays for selected month in database
    cursor.execute(f"SELECT * FROM Birthdays WHERE guildID={interaction.guild.id} " +
        f"AND bday LIKE '%-{currmonth}-%' ORDER BY SUBSTR(bday, 8)")
    rows = cursor.fetchall()

    # If there are birhdays then respond to interaction the birthdays
    if (rows):
        embed = discord.Embed(
        title=f"Birthdays in {curr_month_name}",
        description=f"\nHere are the birthdays in {curr_month_name}!\n",
        color=discord.Color.red())
        file = discord.File("img/birthdaybot.png", filename="birthdaybot.png")
        embed.set_thumbnail(url="attachment://birthdaybot.png")
        val = ""
        for row in rows:
            # Make birthday list
            val += f"  - <@!{row[0]}> ({curr_month_name} {row[3].split('-')[2]})\n"
        if (len(rows) == 1):
            embed.add_field(name=f"**There is 1 birthday in {curr_month_name}:**", value=f"{val}")
        else:
            embed.add_field(name=f"**There are {len(rows)} birthdays in {curr_month_name}:**", value=f"{val}")

        # Add footer
        embed.set_footer(text="If you want your birthday to be added, use the 'b!addbirthday' command!")
        await interaction.response.send_message(file=file, embed=embed)
    else:
        await interaction.response.send_message("There are no birthdays for this month!")

# /fact
@bot.tree.command(name="fact", description="Prints a fact.")
async def fact(interaction: discord.Interaction):
    await interaction.response.send_message(f"<@!{interaction.guild.owner_id}> is acting dictator of {interaction.guild.name}")

# /nextcheck - only for debugging. This checks the bot's next check time accross 
# ALL servers it's connected too.
# @bot.tree.command(name="nextcheck")
# async def fact(interaction: discord.Interaction):
#     await interaction.response.send_message(f"Next check at {bot.birthday_message.next_iteration}.")
#     print(bot.birthday_message.next_iteration)

# /setchannel
@bot.tree.command(name='setchannel', description="Select which channel to send the birthday announcements to.")
@app_commands.checks.has_permissions(manage_guild=True)
async def setchannel(interaction: discord.Interaction, input: str = None):
    cursor = connection.cursor()

    # Check for specified channel
    cursor.execute(f"SELECT * FROM Servers WHERE serverID={interaction.guild_id} AND channelID IS NULL")
    row = cursor.fetchone()
    if (input and re.search(r"^<#\d*>$", input)):
        channelID = int(re.sub('\D', '', input))
        cursor.execute(f"UPDATE Servers SET channelID = '{channelID}' WHERE serverID = {interaction.guild_id}")
        connection.commit()
        await interaction.response.send_message("Channel has been updated.")
    else:
        await interaction.response.send_message("Please enter a valid channel.")

    global announceTime
    announceTime = getAnnounceTime()

# /settime
# TODO localize input instead of using UTC
@bot.tree.command(name='settime', description="Set what time BirthdayBot will announce birthdays daily")
@app_commands.describe(input="Time for daily announcment in military time (e.g. 1400) in UTC.")
@app_commands.checks.has_permissions(manage_guild=True)
async def settime(interaction: discord.Interaction, input: app_commands.Range[int, 0, 2399]):
    bot.birthday_message.cancel()
    print(f"Changing {interaction.guild.name} check time to {input}. The current time is {datetime.now()}")
    cursor = connection.cursor()
    newTime = time(hour=int(input/100), minute=int(input % 100))
    cursor.execute(f"UPDATE Servers SET announceTime = '{newTime}' WHERE serverID = {interaction.guild_id}")
    connection.commit()
    await interaction.response.send_message("The announcement time has been updated")

    global announceTime #this is bad code, TODO fix this garbage
    announceTime = getAnnounceTime()
    bot.birthday_message.change_interval(time=announceOnlyTime())
    bot.birthday_message.start()
    print("Check loop restarted.")


# Incorrect role error message
@bot.event
async def on_command_error(interaction: discord.Interaction, error):
  if isinstance(error, commands.errors.MissingPermissions):
    await interaction.message.send_message('You do not have the permission for this command.', ephemeral=True)
  elif isinstance(error, commands.CommandNotFound):
    await interaction.message.send_message('This command does not exist.', ephemeral=True)

def signal_handler(sig, frame):
    print('Shutting down BirthdayBot')
    bot.close()
    exit(0)

signal(SIGINT, signal_handler)
bot.run(TOKEN)