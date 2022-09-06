import asyncio
import random
import os
from time import strftime,localtime 
from hoshino import Service, priv, sucmd, get_bot
from hoshino.typing import MessageSegment as CommandSession,CQEvent
from hoshino.config import SUPERUSERS
import yaml
from subprocess import Popen





#不要随便把print改成log，因为要读log
#写的代码后面自己都不知道是啥了呜呜呜
sv = Service("冻结自动切号", use_priv=priv.SU, manage_priv=priv.SU, visible=False)
bot = get_bot()
session = None
filename=''
last_filename=''
file_size_flag = 0             #文件大小指针
file_cursor_flag = 0           #上次读取的指针位置
message_blocked_flag = 99      #风控计数器
message_blocked_lock=0       
account_flag=0                 #识别账号是否切换，为什么切换 0：未知，可能是后台自己切的 1：风控/冻结自动切的 2：使用切换账号指令切的
message_blocked_set=10         #风控计数上限
last_line_flag = ""            #log最后一行的内容
qqlist=[]                      #用于缓存正在使用和已切换的qq

file_config = os.path.join(os.path.dirname(__file__),f"config.yml") 
def config_test(file_config):
    with open(file_config, 'r', encoding='utf8') as f:
        return yaml.safe_load(f)

@bot.on_startup
async def start_readlog():
    global session1
    sv.logger.info(f"冻结自动换号程序已开启")         #等待程序加载完ws接上，不然查不到登录信息，虽然会循环查，但是看着
    loop = asyncio.get_event_loop()
    session1 = loop.create_task(readlog())

async def readlog():
    while True:
        try:
            accounts = config_test(file_config).get('list')            #获取gocq和路径
        except Exception as e:
            sv.logger.error(f"{e}config.yml填写不正确！")
            break
        try:
            qqid = (await bot.get_login_info())['user_id']           #获取当前qq
            print('ttttttttttttttttttttttttttttttttttttt')
            qqlist.append(qqid)
        except Exception as e:
            await asyncio.sleep(5)
            continue
        try:
            await get_last_log(accounts,qqid,filename)                #开始读日志，在此循环
        except Exception as e:
            sv.logger.exception(e)
            await asyncio.sleep(15)

async def get_last_log(accounts,qqid,filename):
    """
    打印日志文件的最新内容
    :param filename: 日志文件
    :return: None
    """ 
    global file_size_flag
    global file_cursor_flag
    global last_line_flag
    global message_blocked_flag
    global message_blocked_lock
    global last_filename
    global account_flag
   
    while True:
        try:
            # 获取文件大小
            qq_original=qqid
            qqid = (await bot.get_login_info())['user_id']             
            filename=await get_filename(qqid,accounts)             
            if last_filename=='':
               last_filename=filename
            if last_filename!=filename:
               if account_flag==0:
                  #print(f'原账号{qq_original}因后台切换，现已切换至qq{qqid}')
                  await report_to_su(f'原账号{qq_original}因后台切换，现已切换至qq{qqid}')
            if account_flag==1:
                  #print(f'原账号{qq_original}已被风控/冻结，现已切换至qq{qqid}')
                  account_flag=0
                  await report_to_su(f'原账号{qq_original}已被风控/冻结，现已切换至qq{qqid}')
            if account_flag==2:
                  #print(f'原账号{qq_original}已主动切换至qq{qqid}')
                  account_flag=0
                  await report_to_su(f'原账号{qq_original}已主动切换至qq{qqid}')
            while os.path.isfile(filename)!=True:             #如果过了一天，gocq没有新消息是不会出新的log的
                   sv.logger.info(f"尝试更新今天的日志")
                   if os.path.isfile(filename)!=True:         #没准只是关掉了
                      print("更新失败，300s后重试")
                      await asyncio.sleep(300)
                      return
        except Exception as ret:
            print("错误：", str(ret))
            break
        file_size = os.path.getsize(filename)
        if file_size > file_size_flag:
            file_size_flag = file_size
            with open(filename, 'rb') as f:
                f.seek(file_cursor_flag, 0)  # 移动文件指针到上次读取的位置
                #print('==================开始翻阅===================')
                while True:
                    line = f.readline().decode("utf8")  # 自行修改文件解码格式
                    if line: 
                        if line != last_line_flag:
                            last_line_flag = line
                            if message_blocked_flag!=99:
                                 if '[ERROR]: Protocol -> sendPacket msg error: 46'in last_line_flag and'收到群' not in last_line_flag:
                                    message_blocked_flag+=1                                             #群屏蔽多是这种日志，计数+1
                                 if '[INFO]: 发送群'in last_line_flag:                                 #如果又tm发得出来了，计数清零           
                                    message_blocked_flag=1
                                 if message_blocked_flag==message_blocked_set:                         #超过一定数量发不出视为风控，切号！                                                                                                     
                                    sv.logger.info("tx我cnm,账号怎么被风控了")                                  #同时每天定时清零的
                                    await huanhao(accounts,qqid)
                    else:    #print("已经是最后一行了...")
                        if message_blocked_lock==0:
                            message_blocked_flag=0       #初始化风控读取，这里的最后一行是读取时的最后一行
                            message_blocked_lock=1
                            file_cursor_flag = f.tell()  # 记录当前指针的位置
                            sv.logger.info(f"初始化已完成,指针的位置：{file_cursor_flag}")
                        file_cursor_flag = f.tell()  # 记录当前指针的位置
                        break
                    await asyncio.sleep(0.1)
        if '[FATAL]: 账号被冻结'in last_line_flag and '收到群' not in last_line_flag: #这里的最后一行是真最后一行
              sv.logger.info("tx我cnm,账号怎么被冻结了")
              await huanhao(accounts,qqid)
              break
        #print(message_blocked_flag)
        await asyncio.sleep(60)               #60s开始刷新新日志，可以随意缩短


async def get_filename(qqid,accounts):
    for account in accounts:
            if qqid==account['qq']:
               path=account['path']  
    nowday= strftime("%Y-%m-%d", localtime()) 
    log=f'{nowday}.log'
    filename=f'{path}\\logs\\{log}'
    return filename


async def report_to_su(msg):
    bot = get_bot()
    sid = bot.get_self_ids()
    if len(sid) > 0:
       sid = random.choice(sid)
       await bot.send_private_msg(self_id=sid, user_id=SUPERUSERS[0], message=msg)

async def initialization():
    global file_size_flag      
    global file_cursor_flag    
    global last_line_flag         
    global message_blocked_flag  
    global message_blocked_lock  
    global last_filename
    file_size_flag = 0             #文件大小指针
    file_cursor_flag = 0           #上次读取的指针位置
    last_line_flag = ""            #log最后一行的内容
    message_blocked_flag=99        #风控计数器
    message_blocked_lock=0         #确认风控计数器只执行一次
    last_filename=''

async def zero_clear():
    global message_blocked_flag
    message_blocked_flag=0
    sv.logger.info('风控计数器已清零')

async def huanhao(accounts,qq_original):
    global message_blocked_flag
    global file_size_flag             #文件大小指针
    global file_cursor_flag            #上次读取的指针位置
    global last_line_flag             #log最后一行的内容
    global message_blocked_lock
    global account_flag            
    c = []
    if type(accounts)==list:
      for account in accounts:
          c.append(account['qq'])
      print(f'qqlist{qqlist}')
      c=set(c) ^ set(qqlist)
      c=list(c)
      qqid=c[0]
      account_flag=1
    else:
      qqid=accounts
      accounts = config_test(file_config).get('list') 
      account_flag=2
    path=find_path(accounts,qqid)
    sv.logger.info(f"账号即将切为{qqid}")
    sv.logger.info(f"gocq即将切为路径{path}")
    try:
      os.system('taskkill /f /im go-cqhttp.exe')
      Popen(f"{path}\\go-cqhttp.bat",cwd=f"{path}")
      session1.cancel()
      await initialization()
      await start_readlog()
    except Exception as e:
        sv.logger.exception(e)
        await bot.send(f"Error: {type(e)}")
     


sv.scheduled_job('cron', hour=3, jitter=300)(zero_clear)

@sv.on_fullmatch(('帐号列表','账号列表'))
async def zhanghao_list(bot, ev):
    msg='账号列表如下：\n'
    accounts = config_test(file_config).get('list') 
    for account in accounts:
            qq=account['qq']
            msg+=str(qq)+'\n'
    msg+='已用账号如下：\n'
    for qqid in qqlist:
           msg+=str(qqid)+'\n'
    qqid = (await bot.get_login_info())['user_id'] 
    msg+='当前账号为'+str(qqid)
    await bot.send(ev, msg)

def check_exist(my_list, key):
    for n in my_list:
        if key in n.values():
           return True
    return False

def find_path(my_list, key):
    for n in my_list:
        if key in n.values():
           return n['path']

@sv.on_prefix(('切换账号','切换帐号'))
async def change_zhanghao(bot, ev: CQEvent):
    args = ev.message.extract_plain_text()
    args = int(args)
    accounts = config_test(file_config).get('list')
    check=check_exist(accounts,args)
    if check:
       qq_original = (await bot.get_login_info())['user_id'] 
       await huanhao(args,qq_original)

@sv.on_prefix(('激活账号','激活帐号'))
async def change_zhanghao(bot, ev: CQEvent):
    args = ev.message.extract_plain_text()
    args = int(args)
    qqid = (await bot.get_login_info())['user_id']   
    if args in qqlist:
        if args==qqid:
           await bot.send(ev, '当前账号正在使用中，无需激活')
        else:
           qqlist.remove(args)
           await bot.send(ev, '{args}已激活，将进入自动切号列表')

@sucmd("reload-session1", force_private=False, aliases=("重启切号", "重载切号"))#不知道有啥用
async def reload_session1(session: CommandSession):
    try:
        session1.cancel()
        await initialization()
        await start_readlog()
        await session.send("重载已完成")
    except Exception as e:
        sv.logger.exception(e)
        await session.send(f"Error: {type(e)}")
