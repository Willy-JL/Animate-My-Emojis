# AnimateMyEmojis
Simple and robust Discord bot to allow non Nitro users to use animated emojis and allow "yoinking" other servers' emojis

Code behind [`AnimateMyEmojis#7240`](https://discord.com/oauth2/authorize?client_id=812756332905365504&permissions=1610689600&scope=bot)

## How to use
### Users
- Just send messages containing animated emoji names as if they were normal emojis

  Example: `I'm so hyped for tomorrow's release :aPES_PogHype:`
- The bot will then delete your message and send it again using a custom webhook with all the emojis converted and animated

### Server Staff
- [Invite](https://discord.com/oauth2/authorize?client_id=812756332905365504&permissions=1610689600&scope=bot) the bot to your server
- Make sure the bot has access to the channels where you want it to convert emojis! You can check by looking for it in the members sidebar

### "Yoinking" emojis
This allows you to add emojis from another server to your own server
- Ping the bot and follow that with the emojis to yoink

  Example: `@AnimateMyEmojis :some_emoji: :Some_other_emoji:`
- The "literal" emojis need to be already converted to real emoji format, meaning that `:some_emoji:` in plain text wont work, you should use the built in emoji picker
- Non nitro users can do this using links: right click on the emoji, click "Copy Emoji Link" and use the command with the links

  Example: `@AnimateMyEmojis https://cdn.discordapp.com/emojis/777335122562777108.gif?v=1`
- This command accepts the emojis even when they are mixed ("literal" and link format) and even when they have other gibberish in between

Keep in mind that you will need the `manage emojis` permission to use this feature!

### Set up your own
- Clone the repo
- Set up with Heroku:
  - Push to Heroku
  - Add a config var named "token" containing your bot's token
- Set up manually:
  - Install requirements (`pip install -r requirements.txt`)
  - (Optional) Remove `Procfile` and `runtime.txt` as you won't need them
  - Edit `main.py` near the end:
    - Replace
      ```python
      client.loop.run_until_complete(client.run(os.environ['token']))
      ```
    - With
      ```python
      client.loop.run_until_complete(client.run("YOUR_TOKEN"))
      ```
  - Run `main.py` with Python

## Requirements
- [Python 3.8](https://www.python.org/downloads/)
   - requests (`pip install requests`)
   - discord.py (`pip install discord.py`)
