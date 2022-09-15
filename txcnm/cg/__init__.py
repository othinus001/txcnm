import asyncio
import random
import os
from time import strftime,localtime 
from hoshino import Service, priv, sucmd, get_bot,HoshinoBot
from hoshino.typing import MessageSegment as CommandSession,CQEvent
from hoshino.config import SUPERUSERS
import hashlib
import yaml
from subprocess import Popen
from PIL import Image, ImageDraw, ImageFont
from aiocache import cached
import httpx
from io import BytesIO



#不要随便把print改成log，因为要读log
#没学过python，面向复制粘贴编程，写的太丑别骂了别骂了
#欢迎大佬优化代码，感觉if还是太多了
#整体思路   1.config.yml下填写qq和gocq路径path,   hoshino开启时加载进程session1->启动任务readlog
#           2.获取gocq和路径->获取当前qq->没问题进入循环
#            3.开始读日志，在循环，以下为循环内容
#             4.获取路径文件名，如果和上次循环的不同视为自己主动切号了，重载日志
#              5.利用日志指针，在读取完初始日志后实时读取最后一条消息，最后一条为冻结则切号，刷新日志时风控超过数量切号
sv = Service("冻结自动切号", use_priv=priv.SU, manage_priv=priv.SU, visible=False)
bot = get_bot()
session1 = None                 #本进程初始化
filename=''                    #文件名
last_filename=''               #上次读取的文件名，不同则视为切号
file_size_flag = 0             #文件大小指针
file_cursor_flag = 0           #上次读取的指针位置
message_blocked_flag = 99      #风控计数器
message_blocked_lock=0         #确认风控计数器只运行一次
account_flag=0                 #识别账号是否切换，为什么切换 0：未知，可能是后台自己切的 1：风控/冻结自动切的 2：使用切换账号指令切的
last_line_flag = ""            #log最后一行的内容
qqlist=[]                      #用于缓存正在使用和已切换的qq
qq_original=0                    #缓存上一次读日志时的qq

#########################以上除非看得懂不要乱动，以下随便乱动############################
time_refresh=120               #刷新日志的间隔时间，默认120s刷新一次，当然10s,600s也不是不行，看你服务器和是否需要马上切号
message_blocked_set=10         #风控计数上限，当前还在猜想风控是否是仅发图发不出（需要有人提供这种情况的日志），所以累计10次发不出再切
go_cqhttp_name='go-cqhttp.exe' #你gocq文件夹.exe的名字,为了照顾不愿意改名的同学,我的是go-cqhttp.bat和go-cqhttp.exe,打开bat文本也是go-cqhttp.exe

file_config = os.path.join(os.path.dirname(__file__),f"config.yml") 
def config_test(file_config):
    with open(file_config, 'r', encoding='utf8') as f:
        return yaml.safe_load(f)

@bot.on_startup
async def start_readlog():
    global session1
    sv.logger.info(f"冻结自动换号程序已开启")       
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
            if qqid not in qqlist:
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
    global qq_original
   
    while True:
        try:
            # 获取文件大小
            qqid = (await bot.get_login_info())['user_id']             
            filename=await get_filename(qqid,accounts)            
            if last_filename=='':
               last_filename=filename
            if last_filename!=filename:
               if qq_original!=qqid and account_flag==0:
                  #print(f'原账号{qq_original}因后台切换，现已切换至qq{qqid}')
                  await report_to_su(f'原账号{qq_original}因后台切换，现已切换至qq{qqid}')
               await initialization()
               if qqid not in qqlist:
                  qqlist.append(qqid)
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
            # await asyncio.sleep(300)
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
        qq_original=qqid
        await asyncio.sleep(time_refresh)               #60s开始刷新新日志，可以随意缩短


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
      #print(f'qqlist为{qqlist}')
      c=set(c) ^ set(qqlist)
      c=list(c)
      #print(f'cccccccccccccc为{c}')
      if c==[]:
        sv.logger.info(f"账号已不足切换，保持原状")
        await asyncio.sleep(7200)                  #没号切不了了，进程开摆，有号就重载吧
        return
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
      os.system(f'taskkill /f /im {go_cqhttp_name}')
      Popen(f"{path}\\go-cqhttp.bat",cwd=f"{path}")
      session1.cancel()
      await asyncio.sleep(15)#等一下新cq加载
      await initialization()
      await start_readlog()
    except Exception as e:
        sv.logger.exception(e)
        await bot.send(f"Error: {type(e)}")
     


sv.scheduled_job('cron', hour=3, jitter=300)(zero_clear)



def check_exist(my_list, key):
    for n in my_list:
        if key in n.values():
           return True
    return False

def find_path(my_list, key):
    for n in my_list:
        if key in n.values():
           return n['path']

@sv.on_prefix(('移除账号','移除帐号'),only_to_me=True)
async def yichu_zhanghao(bot, ev: CQEvent):
    args = ev.message.extract_plain_text()
    args = int(args)
    accounts = config_test(file_config).get('list')
    check=check_exist(accounts,args)
    if check: 
       if args in qqlist: 
          await bot.send(ev, f'{args}已在已用列表之中')
       else:
          qqlist.append(args)
          await bot.send(ev, f'已将{args}移入已用列表,不会进入待切号序列')
          

@sv.on_prefix(('切换账号','切换帐号'),only_to_me=True)
async def change_zhanghao(bot, ev: CQEvent):
    args = ev.message.extract_plain_text()
    args = int(args)
    accounts = config_test(file_config).get('list')
    check=check_exist(accounts,args)
    if check:
       qq_original = (await bot.get_login_info())['user_id'] 
       await huanhao(args,qq_original)

@sv.on_prefix(('激活账号','激活帐号'),only_to_me=True)
async def jihuo_zhanghao(bot, ev: CQEvent):
    args = ev.message.extract_plain_text()
    args = int(args)
    qqid = (await bot.get_login_info())['user_id']   
    if args in qqlist:
        if args==qqid:
           await bot.send(ev, '当前账号正在使用中，无需激活')
        else:
           qqlist.remove(args)
           await bot.send(ev, f'{args}已激活，将进入待切号序列')

@sucmd("reload-session1", force_private=False, aliases=("重启切号", "重载切号"))#完全重载，记录清除
async def reload_session1(session: CommandSession):
    global qq_original
    global qqlist
    try:
        session1.cancel()
        await initialization()
        qqlist=[]                    
        qq_original=0 
        await start_readlog()
        await session.send("重载已完成")
    except Exception as e:
        sv.logger.exception(e)
        await session.send(f"Error: {type(e)}")


@sv.on_suffix(('账号列表','帐号列表'))
async def list_help(bot, ev):
    image = Image.open(os.path.join(os.path.dirname(__file__),f"list.png")).convert('RGB')
    draw= ImageDraw.Draw(image) #建立一个绘图的对象
    font = ImageFont.truetype(os.path.join(os.path.dirname(__file__),f"081.ttf"), 85)
    font2 = ImageFont.truetype(os.path.join(os.path.dirname(__file__),f"081.ttf"), 70)
    mask = Image.open(os.path.join(os.path.dirname(__file__),f'mask.png')).convert('RGBA') # 蒙板 
    accounts = config_test(file_config).get('list') 
    if len(accounts)>7:
            msg='账号列表如下：\n'
            for account in accounts:
                qq=account['qq']
                msg+=str(qq)+'\n'
            msg+='已用账号如下\n'
            for qqid in qqlist:
                msg+=str(qqid)+'\n'
            qqid = (await bot.get_login_info())['user_id'] 
            msg+='已用过的不会进入自动换号列表\n激活账号：移出已用列表\n移除账号：移入已用列表\n切换账号：主动，原号移入已用\n当前账号为'+str(qqid)
            await bot.send(ev, msg)
            return
    qqid_now = (await bot.get_login_info())['user_id']    
    n=0  
    r=70                                          
    for account in accounts:
           name=await get_user_info(bot,ev, account['qq'])
           img = await download_avatar(account['qq'])
           if img:
              qq_img=await qqimg(img,mask)
              rs, g, b, a = qq_img.split()
           text1=str(account['qq'])
           if account['qq'] in qqlist and account['qq']!=qqid_now:
              if img:image.paste(qq_img,(697,692+278*n,1147,904+278*n),mask=a)
              draw.ellipse((200-r, 790+278*n-r, 200+r, 790+278*n+r), fill='#d9526b')#红
              draw.text((138,752+278*n), '已用', font=font2, fill="#ffffff") 
              draw.text((340,715+278*n), text1, font=font, fill="#d9526b") 
              draw.text((340,800+278*n), name, font=font2, fill="#000000") 
           elif account['qq'] == qqid_now:
              if img:image.paste(qq_img,(697,692+278*n,1147,904+278*n),mask=a)
              draw.ellipse((200-r, 790+278*n-r, 200+r, 790+278*n+r), fill='#359ee8')#蓝
              draw.text((138,752+278*n), '当前', font=font2, fill="#ffffff")
              draw.text((340,715+278*n), text1, font=font, fill="#359ee8") 
              draw.text((340,800+278*n), name, font=font2, fill="#000000") 
           else:
              if img:image.paste(qq_img,(697,692+278*n,1147,904+278*n),mask=a)
              draw.ellipse((200-r, 790+278*n-r, 200+r, 790+278*n+r), fill='#27cb93')#绿
              draw.text((138,752+278*n), '可用', font=font2, fill="#ffffff") 
              draw.text((340,715+278*n), text1, font=font, fill="#27cb93") 
              draw.text((340,800+278*n), name, font=font2, fill="#000000") 

           n+=1
    image.save(os.path.join(os.path.dirname(__file__),f"list2.jpg"))
    list2=os.path.join(os.path.dirname(__file__),f"list2.jpg")
    await bot.send(ev, CommandSession.image(f'file:///{list2}'))




async def get_user_info(bot: HoshinoBot,ev, user):
    if not user:
        return
    try:
      info = await bot.get_group_member_info(self_id=ev.self_id, group_id=ev.group_id, user_id=int(user)) 
      name = info.get("card", "") or info.get("nickname", "")
    except Exception as e:
      name='未知昵称'
    return(name)


@cached(ttl=60)
async def download_avatar(user_id: str) -> bytes:
    url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"
    data = await download_url(url)
    if not data or hashlib.md5(data).hexdigest() == "acef72340ac0e914090bd35799f5594e":
        url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=100"
        data = await download_url(url)
        if not data:
            raise DownloadError
    return data

async def download_url(url: str) -> bytes:
    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    continue
                return resp.content
            except Exception as e:
                # sv.logger.warning(f"Error downloading {url}, retry {i}/3: {e}")
                print(f"Error downloading {url}, retry {i}/3: {str(e)}")
    raise DownloadError

class DownloadError(Exception):
    pass

async def qqimg(bg,mask):
    x, y = 0, 0
    bg = to_image(bg)# 背景图
    bg = bg.resize((450, 212))
    mask_size = mask.size 
    crop = bg.crop((x, y, x + mask_size[0], y + mask_size[1]))
    m2 = Image.new('RGBA', mask.size) 
    m2.paste(crop, mask=mask)
    return m2


def to_image(data: bytes) -> Image:
    image = Image.open(BytesIO(data))
    image = to_jpg(image).convert("RGBA")
    return image

def to_jpg(frame: Image, bg_color=(255, 255, 255)) -> Image:
    if frame.mode == "RGBA":
        bg = Image.new("RGB", frame.size, bg_color)
        bg.paste(frame, mask=frame.split()[3])
        return bg
    else:
        return frame.convert("RGB")
