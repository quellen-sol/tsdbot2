import asyncio
import requests
import json
import discord
import os
import re
from discord.ext.commands import Bot, Context
from discord_slash import SlashCommand
from dotenv import load_dotenv
from datetime import date, datetime, timedelta, timezone, time

load_dotenv()

# Fields
# backendBase = 'http://localhost:3002'
backendBase = 'https://tsdbackend-production.up.railway.app'
walletLinking = False
whitelistSpots = 1111

# Users
quellen = 416430897894522890
oil = 941423639306321990
cazz = 733199983288909824
nerg = 547196315403026433
puzz = 261914293740634113

admins = [quellen, oil, cazz, nerg, puzz]

# Guilds
TheSolDen = 939765005421785138

# Roles
adminRole = 939768882263117824
modsRole = 939770454456037386

# Channels
successfulLinksChannel = 945904003714261014
linkChannel = 945904467239387186
top10Channel = 979872560747511818
botLogChannel = 982060324603695104

# Stat Channels
whitelistStat = 945909310175739924
totalMemberStat = 945910384026587136
onlineMemberStat = 945910425218863124

allowedLinkChannels = [945904467239387186]

timezoneOffset = -8  # PDT = -8, UTC = 0


class TheReferee(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.statTask = self.loop.create_task(self.updateStats())
        # self.memberTask = self.loop.create_task(self.updateMemberStats())
        self.aggLeaderboardTask = self.loop.create_task(
            self.aggregateLeaderboard())
        self.clearFightCooldownsTask = self.loop.create_task(
            self.clearFightCooldowns())
        self.resetMaxesTask = self.loop.create_task(self.resetMaxes())
        self.snapshotLeaderboardTask = self.loop.create_task(
            self.resetLeaderboard())
        self.resetUpgradeCooldownTask = self.loop.create_task(
            self.resetUpgradeCooldowns())
        self.reprocessUpgradesTask = self.loop.create_task(
            self.reprocessUpgrades())
        self.nextMidnight = self.determineNextMidnight()
        self.nextFriday = self.determineNextFriday()
        self.nextUpgradeReset = self.determineNextFriday(timedelta(minutes=2))
        self.nextReprocessDate = self.determineNextMidnight(
            timedelta(minutes=3))

    def determineNextMidnight(self, offset=timedelta()):
        dt = date.today()
        midnight = offset + \
            datetime.combine(dt, time(12, 1, 0), timezone(
                timedelta(hours=timezoneOffset)))
        while datetime.now(timezone(timedelta(hours=timezoneOffset))) > midnight:
            midnight += timedelta(days=1)
        print(f"Reset time: {midnight}")
        return midnight

    def determineNextFriday(self, offset=timedelta()):
        today = date.today()
        nextFriday = offset + datetime.combine(today + timedelta(days=(
            4-today.weekday()) % 7), time(12, 0, 0), timezone(timedelta(hours=timezoneOffset)))
        while datetime.now(timezone(timedelta(hours=timezoneOffset))) > nextFriday:
            nextFriday += timedelta(days=7)
        print(f"Next Friday: {nextFriday}")
        return nextFriday

    async def reprocessUpgrades(self):
        await self.wait_until_ready()
        while True:
            await asyncio.sleep(10)
            if datetime.now(timezone(timedelta(hours=timezoneOffset))) > self.nextReprocessDate:
                print("Reprocessing upgrades")
                reprocessReq = requests.post(f"{backendBase}/reprocessfailed", headers={
                                             'Content-Type': 'application/json'}, data=json.dumps({'key': apiAccessKey}), timeout=2.0)
                self.nextReprocessDate = self.determineNextMidnight(
                    timedelta(minutes=3))

    async def resetMaxes(self):
        await self.wait_until_ready()
        while True:
            await asyncio.sleep(10)
            if datetime.now(timezone(timedelta(hours=timezoneOffset))) > self.nextMidnight:
                try:
                    print("RESETTING MAXES")
                    resetReq = requests.post(f'{backendBase}/resetmax', headers={
                                             'Content-Type': 'application/json'}, data=json.dumps({'key': apiAccessKey}), timeout=2.0)
                except Exception as e:
                    await self.get_channel(botLogChannel).send(str(e))
                self.nextMidnight = self.determineNextMidnight()

    async def resetLeaderboard(self):
        await self.wait_until_ready()
        while True:
            await asyncio.sleep(10)
            if datetime.now(timezone(timedelta(hours=timezoneOffset))) > self.nextFriday:
                print("snapshotting leaderboard!")
                try:
                    topTenReq = requests.get(f'{backendBase}/gettopten', headers={
                                             'Content-Type': 'application/json'})
                    if topTenReq.status_code == 200:
                        topTenJson = topTenReq.json()
                        channel: discord.TextChannel = self.get_channel(
                            top10Channel)
                        embed = discord.Embed(
                            title=f"Top 10 Leaderboard for {date.today()}", color=0xFF7B00)
                        num = 1
                        for wallet in topTenJson:
                            embed.add_field(
                                name=f"#{num}", value=wallet, inline=False)
                            num += 1
                        await channel.send(f"<@&{adminRole}> <@&{modsRole}>", embed=embed)
                    requests.post(f'{backendBase}/snapshotleaderboard', headers={
                                  'Content-Type': 'application/json'}, data=json.dumps({'key': apiAccessKey}), timeout=1.0)
                except Exception as e:
                    await self.get_channel(botLogChannel).send(str(e))
                self.nextFriday = self.determineNextFriday()

    async def resetUpgradeCooldowns(self):
        await self.wait_until_ready()
        while True:
            await asyncio.sleep(10)
            if datetime.now(timezone(timedelta(hours=timezoneOffset))) > self.nextUpgradeReset:
                print("resetting upgrade cooldowns!")
                try:
                    requests.post(f'{backendBase}/clearupgradecooldowns', headers={
                                  'Content-Type': 'application/json'}, data=json.dumps({'key': apiAccessKey}), timeout=1.0)
                except Exception as e:
                    await self.get_channel(botLogChannel).send(str(e))
                self.nextUpgradeReset = self.determineNextFriday(
                    timedelta(minutes=2))

    async def aggregateLeaderboard(self):
        await self.wait_until_ready()
        while True:
            await asyncio.sleep(120)
            try:
                requests.post(f'{backendBase}/aggregateleaderboard', headers={
                              'Content-Type': 'application/json'}, data=json.dumps({'key': apiAccessKey}), timeout=2.0)
            except Exception as e:
                pass

    async def clearFightCooldowns(self):
        await self.wait_until_ready()
        while True:
            try:
                requests.post(f'{backendBase}/clearfightcooldowns', headers={
                              'Content-Type': 'application/json'}, data=json.dumps({'key': apiAccessKey}), timeout=2.0)
            except Exception as e:
                pass
            await asyncio.sleep(120)

    async def updateStats(self):
        await self.wait_until_ready()
        while True:
            try:
                statReq = requests.get(f'{backendBase}/getstats?key={apiAccessKey}', headers={
                                       'Content-Type': 'application/json'}, timeout=5.0)
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


bot = TheReferee(command_prefix='+', intents=discord.Intents.all())
slash = SlashCommand(bot, sync_commands=True)
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
    if (value < minval):
        return minval
    if (value > maxval):
        return maxval
    return value


@slash.slash(name='linkwallet', description='Link your wallet to The Sol Den', guild_ids=guilds)
async def linkwallet(ctx: Context, wallet):
    await ctx.defer(hidden=True)
    try:
        if isValidWallet(wallet) and walletLinking and ctx.channel.id in allowedLinkChannels:
            discordId = str(ctx.author.id)
            addWalletReq = requests.post(f'{backendBase}/linkdiscord', headers={
                                         'Content-Type': 'application/json'}, data=json.dumps({'discordId': discordId, 'wallet': wallet, 'key': apiAccessKey}))
            addWalletReq.raise_for_status()
            jsonRes = addWalletReq.json()
            if jsonRes['closed']:
                await ctx.send('The whitelist is now full. Wait until the whitelist has an open spot', hidden=True)
            elif jsonRes['exists']:
                await ctx.send(f'You\'ve already linked your wallet!\n\nWallet currently linked: {jsonRes["wallet"]}\n\nUse /unlink to unlink your wallet!', hidden=True)
            else:
                await bot.get_channel(successfulLinksChannel).send(f'{ctx.author.display_name} ({ctx.author.id}) linked wallet: {wallet}')
                await ctx.send(f'Successfully linked wallet: {wallet}', hidden=True)
        elif not ctx.channel.id in allowedLinkChannels:
            await ctx.send(f'You can only link your wallet in the following channels:\n{printListOfChannels(allowedLinkChannels)}', hidden=True)
        else:
            await ctx.send('The wallet you provided is not a valid wallet, or linking is currently disabled!', hidden=True)
    except Exception as e:
        print(e)
        await ctx.send('Error executing command', hidden=True)


@slash.slash(name='check', description='Check your whitelist status!', guild_ids=guilds)
async def checklink(ctx: Context):
    await ctx.defer(hidden=True)
    checkReq = requests.get(
        f'{backendBase}/checklink?key={apiAccessKey}&discordId={str(ctx.author.id)}')
    try:
        checkReq.raise_for_status()
        checkJson = checkReq.json()
        if checkJson['wallet'] != None:
            await ctx.send(f'You are linked with this wallet:\n\n{checkJson["wallet"]}', hidden=True)
        else:
            await ctx.send(f'You are not linked!', hidden=True)
    except Exception as e:
        await ctx.send('Error running command. Server may be down at this time', hidden=True)


@slash.slash(name='manuallink', description='(Admin only) Manually link a member', guild_ids=guilds)
async def manuallink(ctx: Context, user: discord.User, wallet: str):
    await ctx.defer(hidden=True)
    if ctx.author.id in admins:
        linkReq = requests.post(f'{backendBase}/linkdiscord', headers={'Content-Type': 'application/json'},
                                data=json.dumps({'key': apiAccessKey, 'discordId': str(user.id), 'wallet': wallet, 'override': True}))
        if linkReq.status_code == 200:
            await ctx.send(f'Successfully linked {user.display_name} with wallet: {wallet}', hidden=True)
        else:
            await ctx.send(f'Error running command. Send a screenshot to <@!{quellen}>', hidden=True)
    else:
        await ctx.send('You are not admin!', hidden=True)


@slash.slash(name='snapshotleaderboard', description='Take a snapshot of the leaderboard (Quellen Only)', guild_ids=guilds)
async def scleaderboard(ctx: Context):
    await ctx.defer(hidden=True)
    if ctx.author.id == quellen:
        requests.post(f'{backendBase}/snapshotleaderboard', headers={
            'Content-Type': 'application/json'}, data=json.dumps({'key': apiAccessKey}), timeout=1.0)
        await ctx.send("Snapshotting Leaderboard", hidden=True)
    else:
        await ctx.send("You are not Quellen", hidden=True)


@slash.slash(name='unlink', description='Unlink your wallet from The Sol Den', guild_ids=guilds)
async def unlinkwallet(ctx):
    await ctx.defer(hidden=True)
    if ctx.channel.id in allowedLinkChannels:
        try:
            unlinkReq = requests.post(f'{backendBase}/unlinkdiscord', headers={
                                      'Content-Type': 'application/json'}, data=json.dumps({'discordId': str(ctx.author.id), 'key': apiAccessKey}))
            if (unlinkReq.status_code == 200):
                await bot.get_channel(successfulLinksChannel).send(f'{ctx.author.display_name} Unlinked wallet')
                await ctx.send('Successfully unlinked wallet!', hidden=True)
            elif (unlinkReq.status_code == 404):
                await ctx.send('You have not linked a wallet yet!', hidden=True)
            elif (unlinkReq.status_code == 401):
                raise Exception('Invalid key')
            else:
                raise Exception('Idfk man')
        except Exception as e:
            print(e)
            await ctx.send('Error executing command. Contact <@!416430897894522890> if you see this error!', hidden=True)
    else:
        await ctx.send(f'You can only unlink your wallet in <#{linkChannel}>', hidden=True)


@slash.slash(name='reprocessfailedupgrade', description='(Quellen only) Reprocess the current list of failed upgrades', guild_ids=guilds)
async def reprocessUpgrades(ctx: Context):
    await ctx.defer(hidden=True)
    if ctx.author.id == quellen:
        await ctx.send("Reprocessing failed upgrades", hidden=True)
        requests.post(f'{backendBase}/reprocessfailed', headers={
            'Content-Type': 'application/json'}, data=json.dumps({'key': apiAccessKey}))
        await ctx.send("Reprocessing complete", hidden=True)
    else:
        await ctx.send("You are not Quellen", hidden=True)


@slash.slash(name="failedlist", description="Get a list of failed upgrades", guild_ids=guilds)
async def failedList(ctx: Context):
    await ctx.defer(hidden=True)
    # check if in admin list
    if ctx.author.id in admins:
        failedReq = requests.get(f'{backendBase}/failedupgrades', headers={
                                 'Content-Type': 'application/json'}, data=json.dumps({'key': apiAccessKey}))
        if failedReq.status_code == 200:
            failedJson = failedReq.json()
            if len(failedJson) == 0:
                await ctx.send("No failed upgrades!", hidden=True)
            else:
                if (len(str(failedJson)) > 1900):
                    await ctx.send("Too many failed upgrades to display", hidden=True)
                    return
                await ctx.send(json.dumps(failedJson, indent=2), hidden=True)
        else:
            await ctx.send("Error getting failed list", hidden=True)
    else:
        await ctx.send("You are not an admin", hidden=True)

# @slash.slash(name='golink',description='Go link!',guild_ids=guilds)
# async def golinkmsg(ctx):
#     await ctx.send(f'You\'re all set! Make sure to head over to <#{linkChannel}> to link your wallet! If you do not get a response from the bot, you did not do it correctly!!')


@bot.event
async def on_ready():
    print('Referee Bot Online...')

bot.run(os.getenv('token'))
