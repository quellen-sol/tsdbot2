import json
import requests

from discord.ext.commands import Context
from discord_slash import SlashCommand
from bot.bot import *
from bot.config import *
from bot.utils import *

bot = TheReferee(command_prefix='+', intents=discord.Intents.all())
slash = SlashCommand(bot, sync_commands=True)


@slash.slash(name='linkwallet', description='Link your wallet to The Sol Den', guild_ids=guilds)
async def linkwallet(ctx: Context, wallet):
    await ctx.defer(hidden=True)
    try:
        if isValidWallet(wallet) and walletLinking and ctx.channel.id in allowedLinkChannels:
            discordId = str(ctx.author.id)
            addWalletReq = requests.post(f'{TSD_API}/linkdiscord', headers={
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
        f'{TSD_API}/checklink?key={apiAccessKey}&discordId={str(ctx.author.id)}')
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
        linkReq = requests.post(f'{TSD_API}/linkdiscord', headers={'Content-Type': 'application/json'},
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
        requests.post(f'{TSD_API}/snapshotleaderboard', headers={
            'Content-Type': 'application/json'}, data=json.dumps({'key': apiAccessKey}), timeout=1.0)
        await ctx.send("Snapshotting Leaderboard", hidden=True)
    else:
        await ctx.send("You are not Quellen", hidden=True)


@slash.slash(name='unlink', description='Unlink your wallet from The Sol Den', guild_ids=guilds)
async def unlinkwallet(ctx):
    await ctx.defer(hidden=True)
    if ctx.channel.id in allowedLinkChannels:
        try:
            unlinkReq = requests.post(f'{TSD_API}/unlinkdiscord', headers={
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
        requests.post(f'{TSD_API}/reprocessfailed', headers={
            'Content-Type': 'application/json'}, data=json.dumps({'key': apiAccessKey}))
        await ctx.send("Reprocessing complete", hidden=True)
    else:
        await ctx.send("You are not Quellen", hidden=True)


@slash.slash(name="failedlist", description="Get a list of failed upgrades", guild_ids=guilds)
async def failedList(ctx: Context):
    await ctx.defer(hidden=True)
    # check if in admin list
    if ctx.author.id in admins:
        failedReq = requests.get(f'{TSD_API}/failedupgrades', headers={
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
