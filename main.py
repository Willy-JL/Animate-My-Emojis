import re
import os
import discord
import datetime
from discord.ext import tasks
from discord import Forbidden, NotFound


def embed(title, description, footer='AnimateMyEmojis', icon=discord.Embed.Empty, color=(32, 34, 37), color_obj=None):
    embed_to_send = discord.Embed(title=title, description=description, timestamp=datetime.datetime.utcnow(),
                                  color=discord.Color.from_rgb(color[0], color[1], color[2]) if not color_obj else color_obj)
    embed_to_send.set_footer(text=footer, icon_url=icon)
    return embed_to_send


class AnimateMyEmojis(discord.Client):

    async def make_webhook(self, channel):
        chan_webhooks = await channel.webhooks()
        for chan_webhook in chan_webhooks:
            if chan_webhook.user.id == self.user.id:
                webhooks[channel.id] = chan_webhook
                break
        try:
            webhooks[channel.id]
        except KeyError:
            new_webhook = await channel.create_webhook(name='AnimateMyEmojis Webhook',
                                                                reason=f'Webhook for replacing animated emojis, please do not delete!')
            webhooks[channel.id] = new_webhook

    async def on_ready(self):
        print('Logged in as {0}!'.format(self.user))
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'discord open up', start=start_datetime), status=discord.Status.online)
        update_presence_loop.start()

    async def on_message(self, message):
        if message.guild:
            try:
                if isinstance(message.author, discord.Member) and not message.author.premium_since:
                    msg = message.content
                    emoji_count = 0
                    for match in reversed(list(re.finditer(':\w{2,32}:', msg))):
                        if not (msg[match.start() - 1] == '<' and match.start() > 0) and not (msg[match.start() - 2:match.start()] == '<a' and match.start() > 1):
                            emoji_name = msg[match.start() + 1:match.end() - 1]
                            new_emoji = discord.utils.get(message.guild.emojis, name=emoji_name)
                            if new_emoji:
                                new_emoji_text = f'<{"a" if new_emoji.animated else ""}:{new_emoji.name}:{new_emoji.id}>'
                                msg = msg[:match.start()] + new_emoji_text + msg[match.end():]
                                emoji_count += 1
                    if emoji_count > 0:
                        global emojis_today
                        print(f"Converting {emoji_count} emojis for @{message.author} in #{message.channel.name} at [{message.guild.name}]")
                        try:
                            webhooks[message.channel.id]
                        except KeyError:
                            await self.make_webhook(message.channel)
                        try:
                            await webhooks[message.channel.id].send(username=message.author.display_name,
                                                                    avatar_url=message.author.avatar_url,
                                                                    content=msg)
                        except NotFound:
                            del webhooks[message.channel.id]
                            await self.make_webhook(message.channel)
                            await webhooks[message.channel.id].send(username=message.author.display_name,
                                                                    avatar_url=message.author.avatar_url,
                                                                    content=msg)
                        emojis_today += emoji_count
                        await message.delete()
            except Forbidden:
                try:
                    await message.reply('', embed=embed(title='⛔  Error!', description=f'The bot doesn\'t have enough permissions to complete the action!', color=(218, 45, 67)))
                except Forbidden:
                    pass


@tasks.loop(seconds=20)
async def update_presence_loop():
    global cur_presence
    if cur_presence == 0:
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f'{len(client.guilds)} servers', start=start_datetime), status=discord.Status.dnd)
        cur_presence = 1
    elif cur_presence == 1:
        count = 0
        for guild in client.guilds:
            count += guild.member_count
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f'{count} users', start=start_datetime), status=discord.Status.dnd)
        cur_presence = 2
    elif cur_presence == 2:
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=f'{emojis_today} emojis today', start=start_datetime), status=discord.Status.dnd)
        cur_presence = 0


cur_presence = 0
emojis_today = 0
if __name__ == '__main__':
    start_datetime = datetime.datetime.now()
    webhooks = {}
    client = AnimateMyEmojis()
    try:
        client.loop.run_until_complete(client.run(os.environ['token']))
    except RuntimeError:
        pass
    finally:
        client.loop.close()
