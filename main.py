import asyncio, requests, json, discord, os, re
from discord.ext.commands import Bot, Context
from discord_slash import SlashCommand
from dotenv import load_dotenv

load_dotenv()

# Fields
# backendBase = 'http://localhost:3002/'
backendBase = 'https://tsdbackend.herokuapp.com/'
walletLinking = True
whitelistSpots = 500

# Guilds
TheSolDen = 939765005421785138

# Channels
successfulLinksChannel = 945904003714261014
linkChannel = 945904467239387186

# Stat Channels
whitelistStat = 945909310175739924
totalMemberStat = 945910384026587136
onlineMemberStat = 945910425218863124

allowedLinkChannels = [945904467239387186]

class TheReferee(Bot):
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
        self.statTask = self.loop.create_task(self.updateStats())
        self.memberTask = self.loop.create_task(self.updateMemberStats())

    async def updateStats(self):
        await self.wait_until_ready()
        while True:
            try:
                statReq = requests.get(f'{backendBase}getstats?key={apiAccessKey}',headers={'Content-Type':'application/json'})
                statReqJson = statReq.json()
                numWhitelists = statReqJson['whitelists']
                await self.get_channel(whitelistStat).edit(name=f'{clamp(0,whitelistSpots,int(numWhitelists))}/{whitelistSpots} Whitelisted')
            except Exception as e:
                print(e)
            await asyncio.sleep(300)

    async def updateMemberStats(self):
        await self.wait_until_ready()
        while True:
            bwguild: discord.Guild = self.get_guild(TheSolDen)
            totalMems = bwguild.member_count
            onlineCount = 0
            for member in bwguild.members:
                if str(member.status) != 'offline':
                    onlineCount += 1
            await self.get_channel(onlineMemberStat).edit(name=f'Online Members: {onlineCount}')
            await self.get_channel(totalMemberStat).edit(name=f'Total Members: {totalMems}')
            await asyncio.sleep(300)

bot = TheReferee(command_prefix='+',intents=discord.Intents.all())
slash = SlashCommand(bot,sync_commands=True)
guilds = [939765005421785138]
apiAccessKey = os.getenv('accesskey')

walletValidationRegex = re.compile('^[\w^0OIl]{43,44}$')


def isValidWallet(wallet: str):
    return walletValidationRegex.match(wallet) != None

def printListOfChannels(arr: 'list[int]') -> str:
    nst = ''
    for channel in arr:
        nst += f'<#{channel}>\n'
    return nst

def clamp(minval: int, maxval: int, value: int):
    if (value < minval): return minval
    if (value > maxval): return maxval
    return value

@slash.slash(name='linkwallet',description='Link your wallet to The Sol Den',guild_ids=guilds)
async def linkwallet(ctx: Context,wallet):
    await ctx.defer(hidden=True)
    try:
        if isValidWallet(wallet) and walletLinking and ctx.channel.id in allowedLinkChannels:
            discordId = str(ctx.author.id)
            addWalletReq = requests.post(f'{backendBase}linkdiscord',headers={'Content-Type': 'application/json'},data=json.dumps({'discordId': discordId,'wallet':wallet,'key':apiAccessKey}))
            addWalletReq.raise_for_status()
            jsonRes = addWalletReq.json()
            if jsonRes['closed']:
                await ctx.send('The whitelist is now full. Wait until the whitelist has an open spot',hidden=True)
            elif jsonRes['exists']:
                await ctx.send(f'You\'ve already linked your wallet!\n\nWallet currently linked: {jsonRes["wallet"]}\n\nUse /unlink to unlink your wallet!',hidden=True)
            else:
                await bot.get_channel(successfulLinksChannel).send(f'{ctx.author.display_name} ({ctx.author.id}) linked wallet: {wallet}')
                await ctx.send(f'Successfully linked wallet: {wallet}',hidden=True)
        elif not ctx.channel.id in allowedLinkChannels:
            await ctx.send(f'You can only link your wallet in the following channels:\n{printListOfChannels(allowedLinkChannels)}',hidden=True)
        else:
            await ctx.send('The wallet you provided is not a valid wallet, or linking is currently disabled!',hidden=True)
    except Exception as e:
        print(e)
        await ctx.send('Error executing command',hidden=True)

@slash.slash(name='unlink',description='Unlink your wallet from The Sol Den',guild_ids=guilds)
async def unlinkwallet(ctx):
    await ctx.defer(hidden=True)
    if ctx.channel.id in allowedLinkChannels:
        try:
            unlinkReq = requests.post(f'{backendBase}unlinkdiscord',headers={'Content-Type': 'application/json'},data=json.dumps({'discordId': str(ctx.author.id),'key':apiAccessKey}))
            if (unlinkReq.status_code == 200):
                await bot.get_channel(successfulLinksChannel).send(f'{ctx.author.display_name} Unlinked wallet')
                await ctx.send('Successfully unlinked wallet!',hidden=True)
            elif (unlinkReq.status_code == 404):
                await ctx.send('You have not linked a wallet yet!',hidden=True)
            elif (unlinkReq.status_code == 401):
                raise Exception('Invalid key')
            else:
                raise Exception('Idfk man')
        except Exception as e:
            print(e)
            await ctx.send('Error executing command. Contact <@!416430897894522890> if you see this error!',hidden=True)
    else: 
        await ctx.send(f'You can only unlink your wallet in <#{linkChannel}>',hidden=True)

@slash.slash(name='golink',description='Go link!',guild_ids=guilds)
async def golinkmsg(ctx):
    await ctx.send(f'You\'re all set! Make sure to head over to <#{linkChannel}> to link your wallet! If you do not get a response from the bot, you did not do it correctly!!')

@slash.slash(name='ping',description='Ping!',guild_ids=guilds)
async def ping(ctx: Context):
    await ctx.send('Pong!')

@bot.event
async def on_ready():
    print('Referee Bot Online...')

bot.run(os.getenv('token'))