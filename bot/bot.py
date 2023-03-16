import asyncio
import json
import requests
import discord
from discord.ext.commands import Bot
from datetime import date, datetime, timedelta, timezone, time
from bot.config import TSD_API, botLogChannel, apiAccessKey, top10Channel, adminRole, modsRole, timezoneOffset, whitelistStat, TheSolDen, onlineMemberStat, totalMemberStat, whitelistSpots
from bot.utils import *


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
                reprocessReq = requests.post(f"{TSD_API}/reprocessfailed", headers={
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
                    resetReq = requests.post(f'{TSD_API}/resetmax', headers={
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
                    topTenReq = requests.get(f'{TSD_API}/gettopten', headers={
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
                    requests.post(f'{TSD_API}/snapshotleaderboard', headers={
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
                    requests.post(f'{TSD_API}/clearupgradecooldowns', headers={
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
                requests.post(f'{TSD_API}/aggregateleaderboard', headers={
                              'Content-Type': 'application/json'}, data=json.dumps({'key': apiAccessKey}), timeout=2.0)
            except Exception as e:
                pass

    async def clearFightCooldowns(self):
        await self.wait_until_ready()
        while True:
            try:
                requests.post(f'{TSD_API}/clearfightcooldowns', headers={
                              'Content-Type': 'application/json'}, data=json.dumps({'key': apiAccessKey}), timeout=2.0)
            except Exception as e:
                pass
            await asyncio.sleep(120)

    async def updateStats(self):
        await self.wait_until_ready()
        while True:
            try:
                statReq = requests.get(f'{TSD_API}/getstats?key={apiAccessKey}', headers={
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
