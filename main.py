from discord import Forbidden, NotFound, HTTPException
from discord.ext import tasks
import datetime
import discord
import asyncio
import aiohttp
import re
import os
import io


def embed(title="", description="", footer="AnimateMyEmojis", icon=discord.Embed.Empty, color=(32, 34, 37), color_obj=None):
    embed_to_send = discord.Embed(title=title, description=description, timestamp=datetime.datetime.utcnow(),
                                  color=discord.Color.from_rgb(color[0], color[1], color[2]) if not color_obj else color_obj)
    embed_to_send.set_footer(text=footer, icon_url=icon)
    return embed_to_send


class AnimateMyEmojis(discord.Client):

    async def ensure_webhook(self, channel):
        if channel.id in webhook_cache:
            return
        chan_webhooks = await channel.webhooks()
        for chan_webhook in chan_webhooks:
            if chan_webhook.user.id == self.user.id:
                webhook_cache[channel.id] = chan_webhook
                break
        if channel.id in webhook_cache:
            return
        new_webhook = await channel.create_webhook(name="AnimateMyEmojis Webhook",
                                                   reason="Webhook for replacing animated emojis, please do not delete!")
        webhook_cache[channel.id] = new_webhook

    def count_emojis(self, guild, animated):
        count = 0
        for emoji in guild.emojis:
            if emoji.animated == animated:
                count += 1
        return count

    async def on_ready(self):
        print(f"Logged in as {self.user}!")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="discord open up", start=start_datetime), status=discord.Status.online)
        update_presence_loop.start()

    async def on_message(self, message):
        if not message.guild:
            return
        global emojis_today
        try:
            only_ping        = message.content     ==     f"<@!{self.user.id}>"  or message.content     ==     f"<@{self.user.id}>"
            starts_with_ping = message.content.startswith(f"<@!{self.user.id}>") or message.content.startswith(f"<@{self.user.id}>")
            if only_ping:
                await message.reply(embed=embed(title="😎 AnimateMyEmojis",
                                                description="You can **invite me** to __your__ server with __**[this link](https://discord.com/oauth2/authorize?client_id=812756332905365504&permissions=1610689600&scope=bot)**__!\n"
                                                            "__**[Here](https://github.com/Willy-JL/animate-my-emojis)**__ you can find more info *and* my source code!\n"
                                                            "\n"
                                                            "Made with 💙 by [WillyJL](https://linktr.ee/WillyJL)",
                                                color=(93, 173, 236)))
            elif starts_with_ping and not only_ping:
                if message.content.startswith    (f"<@!{self.user.id}>"):
                    content = message.content[len(f"<@!{self.user.id}>"):]
                if message.content.startswith    (f"<@{self.user.id}>"):
                    content = message.content[len(f"<@{self.user.id}>"):]
                literal_regex = "<a?:[A-z 0-9]{2,33}:[0-9]{8,100}>"
                link_regex    = "https:\/\/cdn\.discordapp\.com\/emojis\/[0-9]{8,100}\.[A-z0-9]*"
                if re.search(literal_regex, content) or re.search(link_regex, content):
                    if not message.author.guild_permissions.manage_emojis:
                        await message.reply(embed=embed(title="⛔  No Permission!",
                                                        description="You need the **manage emojis** permission to do that!",
                                                        color=(218, 45, 67)))
                        return
                    elif not message.channel.permissions_for(message.guild.me).manage_emojis:
                        await message.reply(embed=embed(description="⛔  The bot doesn't have the **manage emojis** permission!",
                                                        color=(218, 45, 67)))
                        return
                    await message.add_reaction("🔄")
                    result = ""
                    literal_results = list(dict.fromkeys(re.findall(literal_regex, content)))
                    link_results    = list(dict.fromkeys(re.findall(link_regex,    content)))
                    print(f"Yoinking {len(literal_results) + len(link_results)} emojis for @{message.author} in #{message.channel.name} at [{message.guild.name}]")
                    interrupted = False
                    ignored_existing = []
                    warned_animated_slots = False
                    warned_static_slots   = False
                    for literal_emoji in literal_results:
                        if interrupted:
                            break
                        emoji_id = int(literal_emoji[literal_emoji.rfind(":") + 1:literal_emoji.rfind(">")])
                        emoji_name = literal_emoji[literal_emoji.find(":") + 1:literal_emoji.rfind(":")].replace(" ", "")
                        exists = False
                        for existing_emoji in message.guild.emojis:
                            if existing_emoji.id == emoji_id:
                                exists = True
                                ignored_existing.append(emoji_name)
                                break
                        if not exists:
                            if literal_emoji[1] == "a":
                                if self.count_emojis(message.guild, animated=True) >= message.guild.emoji_limit:
                                    if not warned_animated_slots:
                                        await message.reply(embed=embed(description="⛔  There are no more free animated emoji slots!",
                                                                        color=(218, 45, 67)))
                                        warned_animated_slots = True
                                    continue
                                file_name = f"{emoji_id}.gif"
                            else:
                                if self.count_emojis(message.guild, animated=False) >= message.guild.emoji_limit:
                                    if not warned_static_slots:
                                        await message.reply(embed=embed(description="⛔  There are no more free static emoji slots!",
                                                                        color=(218, 45, 67)))
                                        warned_static_slots = True
                                    continue
                                file_name = f"{emoji_id}.png"
                            async with http_client.get(f"https://cdn.discordapp.com/emojis/{file_name}",
                                                       allow_redirects=True) as resp:
                                img = await resp.read()
                            try:
                                new_emoji = await message.guild.create_custom_emoji(name=emoji_name,
                                                                                    image=img)
                                result += "<"
                                if new_emoji.animated:
                                    result += "a"
                                result += f":{new_emoji.name}:{new_emoji.id}> "
                                emojis_today += 1
                            except HTTPException as e:
                                exc_msg = str(e).lower()
                                if "missing permission" in exc_msg:
                                    await message.reply(embed=embed(description="⛔  The bot doesn't have the **manage emojis** permission!",
                                                                    color=(218, 45, 67)))
                                    interrupted = True
                                elif "maximum number of emoji" in exc_msg:
                                    await message.reply(embed=embed(description="⛔  There are no more free emoji slots!",
                                                                    color=(218, 45, 67)))
                                elif "large" in exc_msg:
                                    await message.reply(embed=embed(description=f"⛔  Emoji \"**{emoji_name}**\" is larger than 256kb!",
                                                                    color=(218, 45, 67)))
                                else:
                                    print(exc_msg)
                                    await message.reply(embed=embed(description=f"⛔  Something went wrong!\n```{exc_msg}```",
                                                                    color=(218, 45, 67)))
                    for link_emoji in link_results:
                        if interrupted:
                            break
                        emoji_id = int(link_emoji[34:link_emoji.rfind(".")])
                        emoji_name = str(emoji_id)
                        exists = False
                        for existing_emoji in message.guild.emojis:
                            if existing_emoji.id == emoji_id:
                                exists = True
                                ignored_existing.append(emoji_name)
                                break
                        if not exists:
                            if link_emoji[-4:] == ".gif":
                                if self.count_emojis(message.guild, animated=True) >= message.guild.emoji_limit:
                                    if not warned_animated_slots:
                                        await message.reply(embed=embed(description="⛔  There are no more free animated emoji slots!",
                                                                        color=(218, 45, 67)))
                                        warned_animated_slots = True
                                    continue
                            else:
                                if self.count_emojis(message.guild, animated=False) >= message.guild.emoji_limit:
                                    if not warned_static_slots:
                                        await message.reply(embed=embed(description="⛔  There are no more free static emoji slots!",
                                                                        color=(218, 45, 67)))
                                        warned_static_slots = True
                                    continue
                            async with http_client.get(link_emoji, allow_redirects=True) as resp:
                                img = await resp.read()
                            try:
                                new_emoji = await message.guild.create_custom_emoji(name=emoji_name,
                                                                                    image=img)
                                result += "<"
                                if new_emoji.animated:
                                    result += "a"
                                result += f":{new_emoji.name}:{new_emoji.id}> "
                                emojis_today += 1
                            except HTTPException as e:
                                exc_msg = str(e).lower()
                                if "missing permission" in exc_msg:
                                    await message.reply(embed=embed(description="⛔  The bot doesn't have the **manage emojis** permission!",
                                                                    color=(218, 45, 67)))
                                    interrupted = True
                                elif "maximum number of emoji" in exc_msg:
                                    await message.reply(embed=embed(description="⛔  There are no more free emoji slots!",
                                                                    color=(218, 45, 67)))
                                elif "large" in exc_msg:
                                    await message.reply(embed=embed(description=f"⛔  Emoji \"**{emoji_name}**\" is larger than 256kb!",
                                                                    color=(218, 45, 67)))
                                else:
                                    print(exc_msg)
                                    await message.reply(embed=embed(description=f"⛔  Something went wrong!\n```{exc_msg}```",
                                                                    color=(218, 45, 67)))
                    await message.add_reaction("👌")
                    if ignored_existing:
                        await message.reply(embed=embed(title="⚠️  Existing Emojis!",
                                                            description=f"The following emojis were ignored because they are from this server:\n`{'`,  `'.join(ignored_existing)}`",
                                                            color=(255, 204, 77)))
                    if result:
                        await message.reply(result)
            else:
                if isinstance(message.author, discord.Member) and not message.author.premium_since:
                    msg = message.content
                    emoji_count = 0
                    for match in reversed(list(re.finditer(":\w{2,32}:", msg))):
                        if (msg[match.start()-1] == "<" and match.start() > 0) or (msg[match.start()-2:match.start()] == "<a" and match.start() > 1):
                            continue
                        emoji_name = msg[match.start()+1:match.end()-1]
                        new_emoji = discord.utils.get(message.guild.emojis, name=emoji_name)
                        if new_emoji:
                            new_emoji_text = f"<{'a' if new_emoji.animated else ''}:{new_emoji.name}:{new_emoji.id}>"
                            msg = msg[:match.start()] + new_emoji_text + msg[match.end():]
                            emoji_count += 1
                    if emoji_count > 0:
                        print(f"Converting {emoji_count} emojis for @{message.author} in #{message.channel.name} at [{message.guild.name}]")
                        await self.ensure_webhook(message.channel)
                        if message.reference:
                            if isinstance(message.reference.resolved, discord.Message):
                                mention = f"\n<@!{message.reference.resolved.author.id}> "
                                if "\n" in message.reference.resolved.content:
                                    reply = "> " + message.reference.resolved.content[:message.reference.resolved.content.find("\n")]
                                else:
                                    reply = "> " + message.reference.resolved.content
                                if len(reply) > (2000 - len(msg) - len(mention)):
                                    reply = reply[:(2000-len(msg))-len(mention)-4] + "..."
                                msg = reply + mention + msg
                        files = []
                        for attachment in message.attachments:
                            fp = io.BytesIO()
                            await attachment.save(fp, use_cached=True)
                            fp.seek(0)
                            files.append(discord.File(fp, filename=attachment.filename,
                                                      spoiler=attachment.is_spoiler()))
                        webhook_msg = None
                        try:
                            webhook_msg = await webhook_cache[message.channel.id].send(username=message.author.display_name,
                                                                                       avatar_url=message.author.avatar_url,
                                                                                       content=msg,
                                                                                       embeds=message.embeds,
                                                                                       files=files,
                                                                                       wait=True)
                        except NotFound:
                            del webhook_cache[message.channel.id]
                            await self.ensure_webhook(message.channel)
                            webhook_msg = await webhook_cache[message.channel.id].send(username=message.author.display_name,
                                                                                       avatar_url=message.author.avatar_url,
                                                                                       content=msg,
                                                                                       embeds=message.embeds,
                                                                                       files=files,
                                                                                       wait=True)
                        if webhook_msg:
                            emojis_today += emoji_count
                            author_id = message.author.id
                            try:
                                await message.delete()
                            except:
                                pass
                            await webhook_msg.add_reaction("🚫")
                            try:
                                await client.wait_for('reaction_add',
                                                      timeout=300,
                                                      check=lambda reaction, user: reaction.message.id == webhook_msg.id and user.id == author_id and str(reaction.emoji) == "🚫")
                                await webhook_msg.delete()
                            except asyncio.TimeoutError:
                                await webhook_msg.clear_reaction("🚫")
        except Forbidden:
            try:
                await message.reply(embed=embed(title="⛔  Error!", description="The bot doesn't have enough permissions to complete the action!", color=(218, 45, 67)))
            except Forbidden:
                pass


@tasks.loop(seconds=15)
async def update_presence_loop():
    global cur_presence
    if cur_presence == 0:
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{len(client.guilds)} servers", start=start_datetime), status=discord.Status.dnd)
        cur_presence = 1
    elif cur_presence == 1:
        count = 0
        for guild in client.guilds:
            count += guild.member_count
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{count} users", start=start_datetime), status=discord.Status.dnd)
        cur_presence = 2
    elif cur_presence == 2:
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=f"{emojis_today} emoji{'s' if emojis_today != 1 else ''} today", start=start_datetime), status=discord.Status.dnd)
        cur_presence = 0


cur_presence   = 0
emojis_today   = 0
http_client    = None
webhook_cache  = {}
start_datetime = datetime.datetime.now()

if __name__ == "__main__":

    client = AnimateMyEmojis()

    async def make_aiohttp_session():
        global http_client
        http_client = aiohttp.ClientSession()
    client.loop.run_until_complete(make_aiohttp_session())

    try:
        client.loop.run_until_complete(client.run(os.environ["token"]))
    except RuntimeError:
        pass
    finally:
        client.loop.close()
