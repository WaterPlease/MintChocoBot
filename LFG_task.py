import asyncio
import datetime
import secrets
import random
import pickle

LFG_tasks = []
regToken = None
tempReg = {-1: None}

#It will be on data base in later release
notiDict = dict() #register channel id to notification channel id
LFG_tasks = [] # set of LFG_task
############
alarm_list = [1,5,10,30]
lfg_config = dict()


class LFG_task:
    def __init__(self,guild,regChn,content,author,startTime,num,joinCode):
        global lfg_config
        self.guild = guild #guild id
        self.regChn = regChn
        self.notChn = notiDict[regChn]
        self.content = content
        self.guardians = [author] #mention string list
        self.leader = author #leader's mention string
        self.startTime = startTime #datetime 객체
        self.num = num #화력팀 인원
        self.joinCode = joinCode
        #finding not used code start
        code = None
        while code is None:
            code = random.randint(1,lfg_config["iLfg_maxCode"])
            for task in LFG_tasks:
                if task.code == lfg_config:
                    code = None
                    break
        self.code = code
        #finding not used code end
        LFG_tasks.append(self)

def needAlarm(lfg):
    global alarm_list
    d = lfg.startTime
    diff = d - datetime.datetime.today()
    for alarm in iter(alarm_list[1:]): #d - datetime.datetime.today() > datetime.timedelta(minutes=10)
        if datetime.timedelta(minutes=alarm,seconds=-lfg_config["iPeriod"]) <= diff and diff <= datetime.timedelta(minutes=alarm,seconds=lfg_config["iPeriod"]):
            return alarm
    if diff < datetime.timedelta(0):
        return -2 #expired task
    return -1 #nothing to do


def lfg_setAlarmLst():
    global alarm_list
    lst = lfg_config["lLfg_alarm"]
    alarm_list = []
    for m in lst.split(","):
        alarm_list.append(int(m))


def notificationMsg_reg(lfg):
    return "".join(
        ["[",str(lfg.code),"] 화력팀\n","화력팀 내용 : ",lfg.content,"\n화력팀장 : ",lfg.leader,
        " | ",str(lfg.num),"인 모집","\n시작시간 : ",lfg.startTime.strftime('%Y-%m-%d %H:%M'),
        "\n합류코드 : ",lfg.joinCode]
        )
def notificationMsg_noti(lfg):
    return "".join(
        ["[",str(lfg.code),"] 화력팀 예약","\n/합류 ",lfg.joinCode,"\n시작시간 : ",
        lfg.startTime.strftime('%Y-%m-%d %H:%M'),
        "\n화력팀 목록 : "]
        )+"|".join(lfg.guardians)+"\n화력팀 내용 : "+lfg.content


def find_channel(client,notiId):
    for guild in iter(client.guilds):
        for channel in iter(guild.text_channels):
            if channel.id == notiId:
                return channel


def periocic_lfg(app):
    ''' find tasks that is need to send notification
    return : (channel, notification message)
    '''
    print("화력팀 예약 자동 알림 시행")
    remove_list = []
    notification_list = []
    for lfg_task in iter(LFG_tasks):
        remain = needAlarm(lfg_task)
        if remain == -1:
            continue
        elif remain == -2:
            remove_list.append(lfg_task)
        elif remain >= 0:
            notification_list.append(
                (find_channel(app,lfg_task.notChn),notificationMsg_noti(lfg_task),remain)
                )
    while len(remove_list) > 0:
        idx = LFG_tasks.index(remove_list[0])
        del LFG_tasks[idx]
        del remove_list[0]
    return notification_list


LFG_service = [ "!lfg_reg","!lfg_notification",
                "!lfg_new","!lfg_list",
                "!lfg_join","!lfg_leave",
                "!lfg_del"]
async def lfg_service_handler(message):
    global LFG_tasks
    global regToken
    global tempReg
    global notiDict
    global LFG_tasks
    if message.content.startswith("!lfg_reg"):
        if regToken is None:
            await message.channel.send("토큰 먼저 등록. 노예한테 문의")
            return None
        args = message.content.split(' ')[1:]
        print(args)
        if len(args) != 1:
            await message.channel.send("usage: !lfg_reg token값")
            return None
        regToken = args[0]
        code = -1
        while code in tempReg:
            code = random.randint(1,100)
        tempReg[code] = message.channel
        regToken = None
        await message.channel.send("".join(["알림방에 복붙: !lfg_notification ",str(code)]))
    elif message.content.startswith("!lfg_notification"):
        args = message.content.split(' ')[1:]
        if len(args) != 1:
            await message.channel.send("usage: !lfg_notification <1~100>")
            return None
        code = int(args[0])
        if not code in tempReg:
            await message.channel.send("코드 잘못 됐거나 화력팀 등록 채널 먼저 등록ㄱㄱ")
            return None
        regChannel = tempReg[code]
        notChannel = message.channel
        notiDict[regChannel.id] = notChannel.id
        del tempReg[code]
        await message.channel.send("등록/알림방 지정 완료")
    elif message.content.startswith("!lfg_new"):#!화력팀생성 
        if not message.channel.id in notiDict:
            await message.channel.send("화력팀등록방이 아님ㅇㅇ")
            return None
        args = message.content.split(' ')[1:]
        if len(args)<=3:
            await message.channel.send("usage: !lfg\_new yyyy-mm-dd HH:MM 참여인원 joinCode 화력팀목적")
            return None
        d = None
        joinCode = None
        try:
            d = datetime.datetime.strptime(" ".join(args[0:2]), '%Y-%m-%d %H:%M')
            num = int(args[2])
            joinCode = args[3]
            int(joinCode)
        except ValueError:
            await message.channel.send("usage: !lfg_new yyyy-mm-dd HH:MM 참여인원 joinCode 화력팀_목적")
            return None
        if not d - datetime.datetime.today() > datetime.timedelta(minutes=lfg_config["iLfg_newTaskTime"]): #10분 뒤부터 예약 가능
            await message.channel.send("등록 시간 기준 "+str(lfg_config["iLfg_newTaskTime"])+"분 뒤 일정만 예약 가능")
            return None
        guild = message.channel.guild.id
        lfg = LFG_task(guild,message.channel.id," ".join(args[4:]),message.author.mention,d,num,joinCode)
        await message.channel.send(notificationMsg_reg(lfg))
    elif message.content.startswith("!lfg_list"): #자리 남은 것만 보여줌 또는 특정 예약만 보여줌
        args = message.content.split(' ')[1:]
        if len(args) == 1:
            code = int(args[0])
            for task in iter(LFG_tasks): #다른 디코 서버의 예약도 공유 가능
                if task.code == code:
                    await message.channel.send(notificationMsg_noti(task))
        elif len(args) == 0:
            anyTask=False
            for task in iter(LFG_tasks):
                if task.num > len(task.guardians) and message.channel.guild.id == task.guild and\
                        task.startTime - datetime.datetime.today() > datetime.timedelta(0): #해당 디코 서버이면서 시작 시간이 지나지 않은 예약만 나열함
                    anyTask = True
                    await message.channel.send(notificationMsg_noti(task))
            if not anyTask:
                await message.channel.send("현재 예약 없음")
        else:
            await message.channel.send("!lfg_list 예약코드 or !lfg_list")
    elif message.content.startswith("!lfg_join"):
        args = message.content.split(' ')[1:]
        if len(args) != 1:
            await message.channel.send("!lfg_join 예약코드")
            return None
        code = int(args[0])
        for task in iter(LFG_tasks):
            if task.code == code:
                if task.num <= len(task.guardians):
                    await message.channel.send("예약 인원 가득 참")
                    return None
                else:
                    if message.author.mention in task.guardians:
                        await message.channel.send("이미 예약되어 있음")
                        return None
                    else:
                        task.guardians.append(message.author.mention)
                        await message.channel.send("예약 완료")
                        await message.channel.send(notificationMsg_reg(task))
                        return None
        await message.channel.send("잘못된 예약 코드")
    elif message.content.startswith("!lfg_leave"):
        args = message.content.split(' ')[1:]
        if len(args) != 1:
            await message.channel.send("!lfg_leave 예약코드")
            return None
        code = int(args[0])
        for task in iter(LFG_tasks):
            if task.code == code:
                if message.author.mention in task.guardians:
                    idx = task.guardians.index(message.author.mention)
                    del task.guardians[idx]
                    await message.channel.send("예약 취소됨")
                    await message.channel.send(notificationMsg_reg(task))
                    return None
                else:
                    await message.channel.send("잘못된 예약 코드")
                    return None
        await message.channel.send("잘못된 예약 코드")
    elif message.content.startswith("!lfg_del"):
        args = message.content.split(' ')[1:]
        if len(args) != 1:
            await message.channel.send("!lfg_del 예약코드")
            return None
        code = int(args[0])
        for task in iter(LFG_tasks):
            if task.code == code:
                if task.leader != message.author.mention and message.author.id != lfg_config["iAdminId"]:
                    await message.channel.send("화력팀장만 삭제 가능")
                    return None
                task.startTime = datetime.datetime.today()+datetime.timedelta(hours=-1) #시작시간을 만료된 시간으로 설정
                await message.channel.send("예약 삭제 완료")
                return None


LFG_debug = ["!lfg_status","!lfg_regToken","!lfg_backup","!lfg_load"]
async def lfg_debug_handler(message):
    global LFG_tasks
    global regToken
    global tempReg
    global notiDict
    global LFG_tasks
    #check author is developer
    if message.author.id != lfg_config["iAdminId"]:
        return None
    if message.content == "!lfg_status":
        print("notiDict")
        print(notiDict)
        print("LFG_tasks")
        print(LFG_tasks)
        print("LFG Config")
        print(lfg_config)
    elif message.content == "!lfg_regToken":
        regToken = secrets.token_urlsafe(16)
        await message.channel.send(regToken)
    elif message.content == "!lfg_backup":
        with open("notiDict.pk","wb") as f:
            pickle.dump(notiDict,f)
        with open("LFG_tasks.pk","wb") as f:
            pickle.dump(LFG_tasks,f)
        await message.channel.send("백업완료")
    elif message.content == "!lfg_load":
        try:
            with open("notiDict.pk","rb") as f:
                notiDict=pickle.load(f)
        except:
            notiDict=dict()
            await message.channel.send("notiDict 불러오기 실패")
        try:
            with open("LFG_tasks.pk","rb") as f:
                LFG_tasks=pickle.load(f)
        except:
            LFG_tasks = []
            await message.channel.send("notiDict 불러오기 실패")
        await message.channel.send("불러오기 완료")


def register_lfg(serviceDict):
    global LFG_service
    serviceDict["LFG_service"]=(LFG_service,lfg_service_handler)
    serviceDict["LFG_debug"]=(LFG_debug,lfg_debug_handler)