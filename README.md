# 风控冻结自动切号插件(谁能想个优雅的名字)
##  亲，发色图被冻你还在被人催修?
##  亲，群消息被屏蔽你几天后才发现?
##  亲，会战风控你却在上班/睡觉，没办法修机器人?
为了解决客户的需求(虽然都是来白嫖的客户)，本功能应运而生  
有人问你有那么多号吗？其实2-3个号即可撑起循环，尤其会战这种急需环境，除非你天天发r18色图    
我个人是一个群放三个，随时备用,会长再也不用担心打不了公会战了  
保1200公会招人联系我qq1280224133，还没满嘤嘤嘤  
公会战用yobot的可以看看我的[出刀记录图片版插件](https://github.com/othinus001/Daidao/)    
点个star让我知道有人在用才有动力更(   

本插件使用[GLWTPL(Good Luck With That Public License)](https://github.com/me-shaon/GLWTPL)开源，即： 
- 1.代码处于可用或不可用状态，没有第三种情况。  
- 2.版权所有© 每个人，除了作者  
- 3.在不导致作者被指责或承担责任的情况下，你可以做任何你想要做的事情。  
- 4.祝你好运 

## 最后的碎碎念（希望不要有bug了）  
本项目接近开发完成（不想动了），linux好久没碰一年多卸掉忘光了，写了也没法调试，自己也用不上，所以Linux路径问题自行修改或pr捏        
因为本功能是打开bat运行gocq，没法杀特定路径gocq因为本质是bat不是exe，所以我把gocq同名进程全杀了再切，希望有大佬教下      
多gocq暂时不打算支持了，因为打算重构但是得明年一月了，到时会多cq一体化    
可以关注下 [issue#2](https://github.com/othinus001/txcnm/issues/2#issue-1370783072)的大佬[@Lanly109](https://github.com/Lanly109)的多cq项目进程，如果他做好了我又可以摸了   
最后吐槽一句没人用yobot打公会战了吗，怎么这项目star比我的出刀表插件那么快    

 
## 9.15更新
1.除账号列表指令外，激活账号/移除账号/激活账号都必须@bot（考虑到开发者测试群可能同时几个bot）    
2.给账号列表做了个很cool的界面，可惜不会html只好慢慢pil了，流下菜鸡的泪水，代码借鉴自[头像表情包插件](https://github.com/Lanly109/headimg_generator)     
3.切号增加延时判断，担心有的电脑太垃圾加载慢   


## 9.10更新
修复账号列表重复问题，
对安装方法进行了更详细的解释

# 已知问题  
没有问题！因为刚发，有问题赶紧提issue！不然我真的会忘了代码怎么写的  
暂不支持同时多gocq连一个hoshino，因为没试过，欢迎pr   
请确定填写时账号都非冻结状态，最好都登上去试试  
下一次更新预计明年一月，对项目重构使其和内置go-cqhttp的插件达成完美配合  


# 使用方法 

| 关键词     | 作用     |
| :-------------: | :-------------:|
|(被动)风控超过默认10次  | 切号！从自动切号列表按顺序切，原号进入已用名单
|(被动)账号已冻结       | 切号！从自动切号列表按顺序切，原号进入已用名单   
|切换账号 123456 |主动切换账号，被切的会被加入已用名单，不会进入自动切号列表
|激活账号 123456 |把账号从已用名单移除，重新加入自动切号列表
|账号列表  | 看看现在账号有啥        
|重载切号  |初始化everything

# 安装方法：  
1.复制整个文件夹放进modules，路径为\modules\txcnm\cg\\_init_.py  
2.填写config.yml,照格式添加，需包括当前使用的账号，path下需要有go-cqhttp.bat和logs文件夹  
3.请确认path下的.exe名字，本项目默认名字为go-cqhttp.exe(有的人下载新版本没删go-cqhttp后面的）  
  改了点bat运行不了看下面答疑，如果你死活不想改也没关系看看py可以设置      
4.pip install pyyaml    
5.bot设置加入txcnm    
安装实在是太简单了，很符合我对未来生活的想象，科技并带着偷懒。
# 可能的问题：
Q：当前账号需要填第一个吗？  
A：没有要求，怎么填都行  
Q：我不是冻结只是后台切号怎么办？  
A：想到了，会自动读取新日志  
Q：切号发现后面的号也冻结了？  
A：虽然可以超时判断但感觉没必要，所以开摆，欢迎pr  
Q：刷新日志时间还是太慢了？  
A：py里有可以设置的时间，原120s改成10s也行  
   因为指针读取，内存占用其实不大，不过时间太短的建议给设了令牌桶的+1  
Q：我exe改名go-cqhttp.exe以后bat运行不了了？    
A：你可以用记事本打开bat看看文件名，要确保 bat里的名，.exe名，py里的设置名（默认go-cqhttp.exe）三个必须一致  
Q：我不仅用gocq还用其他的比如yunzai怎么办?    
A：你可以用在项目里搜popen，本质是换号后打开bat，你可以加一条，不会？不会就别动  

# 温馨提示：
如果是冻结一般都会直接告诉你能不能解  
如果是群消息被屏蔽的状态：
用机器人查询地址：https://accounts.qq.com/safe/message/unlock?lock_info=5_1  
最后一个数字1-5都试一遍，有可能能直接解除

