# hypealert

Bot de Discord que avisa cuando un streamer se pone en vivo.

## Instalar

```
pip install -r requirements.txt
```

## Configurar

Copia `.env.example` a `.env` y llena tus datos:

```
BOT_TOKEN=
CHANNEL_ID=
WHOWATCH_STREAMERS=id|nombre|1
KICK_STREAMERS=username|nombre|1
```

El ultimo numero es si menciona @everyone o no (1 o 0). Si tienes mas de uno, sepáralos con coma.

## Correr

```
python bot.py
```

## Licencia

MIT
