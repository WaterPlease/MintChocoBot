import asyncio
import discord

app = discord.Client()
bot_config = dict()
serviceDict = dict()
from LFG_task import periocic_lfg, lfg_config, lfg_setAlarmLst, register_lfg

def find_service(message):
    handler = None
    for v in serviceDict.values():
        cmd = message.content.split(' ')[0].strip()
        if cmd in v[0]:
            handler = v[1]
    return handler


async def bot_debug_handler(message):
    #check author is developer
    global app
    if message.author.id != bot_config["iAdminId"]:
        return None
    if message.content.startswith("!test"):
        await message.channel.send("No problem!")
    elif message.content == "!author.id":
        await message.channel.send(message.author.id)
bot_debug = ["!test","!author.id"]
serviceDict["bot_debug"] = (bot_debug,bot_debug_handler)


async def periocic():
    global app
    global bot_config
    while True:
        #Periodic job for LFG_task service start
        notification_lst = periocic_lfg(app)
        for n in iter(notification_lst):
            await n[0].send(n[1])
        #Periodic job for LFG_task service end
        await asyncio.sleep(bot_config["iPeriod"])


@app.event
async def on_ready():
    print("Log in to discord")
    app.loop.create_task(periocic())
    await app.change_presence(status=discord.Status.online,activity=discord.Game("Destiny2"))


@app.event
async def on_message(message):
    if message.author.bot:
        return None
    handler = find_service(message)
    if handler is None:
        return None
    else:
        await handler(message)


config_dict = dict()
config_dict["@bot"]=bot_config
config_dict["@LFG"]=lfg_config
def loadConfig():
    global config_dict
    config = None
    with open("info.cfg",encoding="utf-8") as f:
        lines = f.readlines()
        for line in iter(lines):
            if line.startswith("#"):
                continue
            line = line.split("#")[0]
            if line.startswith("@"):
                config = config_dict[line.strip()]
                continue
            pair = [x.strip() for x in line.split("=")]
            if pair[0].startswith("i"):
                config[pair[0]] = int(pair[1])
            elif pair[0].startswith("f"):
                config[pair[0]] = float(pair[1])
            elif pair[0].startswith("s"):
                config[pair[0]] = pair[1]
            elif pair[0].startswith("l"):
                config[pair[0]] = pair[1]


def LaunchApp(app):
    global bot_config
    loadConfig()
    # LFG initialization start
    register_lfg(serviceDict)
    lfg_setAlarmLst()
    # LFG initialization end
    print("Token : "+bot_config["sToken"])
    app.run(bot_config["sToken"])


LaunchApp(app)