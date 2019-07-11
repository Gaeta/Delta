from collections import namedtuple

# ---- Misc ----

# Bot presence
Presence = namedtuple("Presence", "activity, status")

# Configured colours
Colours = namedtuple("Colours", "embed, error, ban, unban, mute, unmute, kick")

# Configured roles
Roles = namedtuple("Roles", "admin, mod, muted, member, off_duty, staff, support, pings")

# Configured emojis
Emojis = namedtuple("Emojis", "online, idle, dnd, offline, streaming, text_channel, voice_channel, green_tick, red_tick, gray_tick, bot_tag")

# Configured channels
Channels = namedtuple("Channels", "user_log, mod_log, announcements")

# Case
Case = namedtuple("Case", "mod, user, case, message, punishment, reason")

# Tag
Tag = namedtuple("Tag", "owner, name, content")

# ---- Auto ----

# Anti Spam
AntiSpam = namedtuple("AntiSpam", "enabled, bypassed_channels, threshold_seconds")

# Anti Slur
AntiSlur = namedtuple("AntiSlur", "enabled, bypassed_channels")

# Anti Invite
AntiInvite = namedtuple("AntiInvite", "enabled, bypass_verified, bypassed_channels, bypassed_invites")

# Anti NSFW
AntiNSFW = namedtuple("AntiNSFW", "enabled, bypassed_channels, extra_links")

# Anti Link
AntiLink = namedtuple("AntiLink", "enabled, bypassed_channels, bypassed_links")

# Punishment

AutoMod = namedtuple("AutoMod", "enabled, action")