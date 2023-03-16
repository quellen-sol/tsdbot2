import os
from dotenv import load_dotenv

load_dotenv()

# Fields
TSD_API = os.getenv("apiUrl")
apiAccessKey = os.getenv('accesskey')
walletLinking = False
whitelistSpots = 1111
timezoneOffset = -8  # PDT = -8, UTC = 0

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

allowedLinkChannels = [linkChannel]
guilds = [TheSolDen]
