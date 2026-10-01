# hypealert

Discord bot that monitors Whowatch streamers and sends notifications when they go live. Optional support for Kick streamers.

## Install

```bash
pip install -r requirements.txt
```

## Configure

Copy `.env.example` to `.env` and fill in your data:

```env
BOT_TOKEN=
CHANNEL_ID=
WHOWATCH_STREAMERS=id|name|1
KICK_STREAMERS=username|name|1
```

The last number determines whether it mentions @everyone or not (1 or 0). If you have more than one, separate them with commas.

## Run

```bash
python bot.py
```

## License

MIT

