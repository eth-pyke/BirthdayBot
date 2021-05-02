# bot.py
import os
import sqlite3
import re

import discord
from dotenv import load_dotenv
from discord.ext import commands, tasks
from datetime import datetime
import dateutil
from dateutil.parser import parse

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

MONTHS = {1:31, 2:29, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
MONTH_NAMES =['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

# Command prefix
bot = commands.Bot(command_prefix='b!')

# Connect db
connection = sqlite3.connect("BirthdayBot.db")

@bot.event
async def on_ready():
    print(discord.Client().guilds)
    for g in discord.Client().guilds:
        print(f'{bot.user.name} has connected to {g.name}!\n')

@bot.event
async def on_disconnect():
    print(f'{bot.user.name} has disconnected.')
    # connection.close()

@bot.event
async def on_resumed():
    print(f'{bot.user.name} has reconnected.')
#     connection = sqlite3.connect("BirthdayBot.db")

# When bot first joins and leaves the server
@bot.event
async def on_guild_join(guild):
    print(guild.id)
    print(guild.name)
    cursor = connection.cursor()
    cursor.execute(f"INSERT INTO Servers VALUES({guild.id},'{guild.name}', NULL)")
    connection.commit()
@bot.event
async def on_guild_remove(guild):
    print(guild.id)
    print(guild.name)
    cursor = connection.cursor()
    cursor.execute(f"DELETE FROM Servers WHERE serverID = {guild.id}")
    cursor.execute(f"DELETE FROM Birthdays WHERE guildID = {guild.id}")
    connection.commit()

@bot.command(name='addbirthday', help="Add birthday with date in YYYY-MM-DD format.")
async def addbirthday(ctx, input=None):
    cursor = connection.cursor()

    # Check for specified channel
    cursor.execute(f"SELECT * FROM Servers WHERE serverID={ctx.guild.id} AND channelID NOT NULL")
    row = cursor.fetchone()
    if (not row):
        await ctx.send("Please use the `b!setchannel` command before using this.")
    else:
        if input and re.search(r"^\d{4}-\d{2}-\d{2}$", input):
            date = input.split('-')
            year = int(date[0])
            month = int(date[1])
            date = int(date[2])
            curryear = datetime.now().date().year

            if ((year < curryear - 100 or year > curryear) or (month < 1 or month > 12) or (date < 1 or date > MONTHS[month])):
                await ctx.send('Please enter a valid date.')
            else:
                userID = int(ctx.author.id)
                userName = ctx.author.name
                bday = input
                cursor.execute(f"SELECT * FROM Birthdays WHERE userID={userID} AND guildID={ctx.guild.id}")
                row = cursor.fetchone()
                if row:
                    await ctx.send('You have already added a birthday. Use b!update to change it!')
                else:
                    cursor.execute(f"INSERT INTO Birthdays VALUES ({userID}, {ctx.guild.id}, '{userName}', '{bday}')")
                    connection.commit()
                    await ctx.send('Birthday added successfully')
        else:
            await ctx.send('Either you did not provide a birthday or the date was not formatted like YYYY-MM-DD.')

@bot.command(name='update', help="Add birthday with date in YYYY-MM-DD format.")
async def update(ctx, input=None):
    cursor = connection.cursor()
    if input and re.search(r"^\d{4}-\d{2}-\d{2}$", input):
        date = input.split('-')
        year = int(date[0])
        month = int(date[1])
        date = int(date[2])
        curryear = datetime.now().date().year

        if ((year < curryear - 100 or year > curryear)  or (month < 1 or month > 12) or (date < 1 or date > MONTHS[month])):
            await ctx.send('Please enter a valid date.')
        else:
            userID = int(ctx.author.id)
            userName = ctx.author.name
            bday = input
            cursor.execute(f"SELECT * FROM Birthdays WHERE userID={userID} AND guildID={ctx.guild.id}")
            row = cursor.fetchone()
            if not row:
                await ctx.send('Use addbirthday command instead.')
            else:
                cursor.execute(f"UPDATE Birthdays SET bday = '{bday}' WHERE USERID = {userID} AND guildID={ctx.guild.id}")
                connection.commit()
                await ctx.send('Birthday updated successfully.')
    else:
        await ctx.send('Either you did not provide a birthday or the date was not formatted like YYYY-MM-DD.')

@bot.command(name='month', help="Sees who has birthdays this month. Choose which month you want to see using the numbers 1-12 or leave it blank to see the current month.")
async def month(ctx, input=None):
    cursor = connection.cursor()

    currmonth = 0
    curr_month_name = ""
    if (input):
        if (int(input) > 0 and int(input) <= 12):
            curr_month_name = MONTH_NAMES[int(input) - 1]
            if int(input) < 10:
                currmonth = f'0{input}'
            else:
                currmonth = input
        else:
            await ctx.send("Please enter a valid number from 1-12.")
            return
    else:
        currmonth = datetime.now().date().month
        curr_month_name = MONTH_NAMES[currmonth - 1]
        if currmonth < 10:
            currmonth = f'0{currmonth}'
    cursor.execute(f"SELECT * FROM Birthdays WHERE guildID={ctx.guild.id} AND bday LIKE '%-{currmonth}-%' ORDER BY SUBSTR(bday, 8)")
    rows = cursor.fetchall()
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
        await ctx.send(file=file, embed=embed)
    else:
        await ctx.send("There are no birthdays for this month!")

@bot.command(name='fact')
async def fact(ctx):
    await ctx.send(f"<@!{ctx.guild.owner_id}> is acting dictator of {ctx.guild.name}.")

@bot.command(name='setchannel', help="Select which channel to send the birthday announcements to.")
@commands.has_permissions(manage_guild=True)
async def setchannel(ctx, input=None):
    cursor = connection.cursor()

    # Check for specified channel
    cursor.execute(f"SELECT * FROM Servers WHERE serverID={ctx.guild.id} AND channelID IS NULL")
    row = cursor.fetchone()
    if (input and re.search(r"^<#\d*>$", input)):
        channelID = int(re.sub('\D', '', input))
        cursor.execute(f"UPDATE Servers SET channelID = '{channelID}' WHERE serverID = {ctx.guild.id}")
        connection.commit()
        await ctx.send("Channel has been updated.")
    else:
        await ctx.send("Please enter a valid channel.")

# Incorrect role error message
@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.errors.CheckFailure):
    await ctx.send('You do not have the correct role for this command.')
  elif isinstance(error, commands.CommandNotFound):
    await ctx.send('This command does not exist. Please use b!help to see valid commands.')

@tasks.loop(hours=24)
async def birthday_message():
    cursor = connection.cursor()
    cursor.execute(f"SELECT channelID FROM Servers WHERE channelID NOT NULL")
    channels = cursor.fetchall()

    for channel in channels:
        message_channel = bot.get_channel(int(channel[0]))

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
                if (row[0] == 344712385287684097):
                    val += f"  - Our Supreme Dictator <@!{row[0]}> is turning {age} years old! :prince: :skull_crossbones:\n"
                else:
                    val += f"  - <@!{row[0]}> is turning {age} years old! :confetti_ball:\n"
            val +="\nMake sure to wish them a Happy Birthday!"
            if (len(rows) == 1):
                embed.add_field(name=f"**There is 1 birthday today:**", value=f"{val}")
            else:
                embed.add_field(name=f"**There are {len(rows)} birthdays today:**", value=f"{val}")

            # Add footer
            embed.set_footer(text="If you want everyone to be notified of your birthday, use 'b!addbirthday' to be added!")
            await message_channel.send(f"@everyone \n<@!826677529451954177> here with a Special **Birthday Announcement**!", file=file, embed=embed)

@birthday_message.before_loop
async def before():
    await bot.wait_until_ready()
    print("Finished waiting")

birthday_message.start()

bot.run(TOKEN)