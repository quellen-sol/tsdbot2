import re
from bot.config import *


def isValidWallet(wallet: str):
    walletValidationRegex = re.compile('^[\w^0OIl]{43,44}$')
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
