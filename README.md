# Delta

Delta was originally made by JackTEK#6669 & Nope#2019 using [discord.py](https://pypi.org/project/discord.py) as a submission for the Discord Hack Week project: [DisBot](https://github.com/disbotdiscord/DisBot/), but was later re-purposed into a fully-fledged open-source bot. It is designed to help manage [Mila Software](https://invite.gg/mila)!

## Setup

To setup Delta, simply clone this repository and move it to a safe area. Once you've done that:
- Rename the `config.example.json` to `config.json` 
- Edit any settings within the file 
- Make sure the database's directory exists. 
- Run `pip3 install pyfiglet`
- Start the bot, to do this, cd into the directory and run `python3 Bot.py`

## Documentation

Below you can find the documentation for Delta to make usage much easier!

### Features

Here's a list of every feature you can expect to see in Delta:
+ Extensive configurability 
+ Easily modifiable 
+ Clean and optimised code 
+ Easy-to-setup automatic moderator 
+ Automatic user join/leave & punishment logging 
+ Mods logs have an editable reason and can be fetched via a command
+ On/Off Duty system designed to reduce the amount of DMs and pings that staff get
+ Pingmod command that pings a random, on-duty mod that is neither idle nor offline

### Commands

Here's a list of commands that you will find in Delta, you can also use `db.help`:
- Basic
```python
> case
- Gets information on a case.

> devs
- Lists the original developers.

> help
- Shows the help list.

> ping 
- Shows connection latency.

> pingmod
- Picks an on-duty staff member at random and pings them.

> polls
- Toggles the poll/announcement ping role.

> staff
- Shows a list of staff members.
```

- Moderator
```python
> ban
- Bans up to 5 users.

> bans
- Lists up to 20 bans.

> duty
- Togggles your duty status.

> hackban
- Bans up to 5 users via IDs.

> kick
- Kicks up to 5 users.

> mute
- Mutes up to 5 users.

> purge
- Deletes up to 200 messages.

> unban
- Unbans up to 5 users via IDs.

> unmute
- Unmutes up to 5 users.
```

- Administrator
```python
> announce
- Creates an announcement message.

> lockdown
- Starts/lifts a channel lockdown.

> poll
- Creates a poll with up to 5 answers.

> reload
- Reloads the config.json file.

> resetid
- Wipes all of the mod-log data.
```
