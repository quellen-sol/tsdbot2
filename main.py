import os
from bot.commands import *;

@bot.event
async def on_ready():
    print('Referee Bot Online...')

bot.run(os.getenv('token'))
