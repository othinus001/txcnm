# 风控冻结自动切号插件(谁能想个优雅的名字)
##  亲，发色图被冻你还在被人催修?
##  亲，群消息被屏蔽你几天后才发现?
##  亲，会战风控你却在上班/睡觉，没办法修机器人?
为了解决客户的需求(虽然都是来白嫖的客户)，本功能应运而生  
有人问你有那么多号吗？其实2-3个号即可撑起循环，尤其会战这种急需环境，除非你天天发r18色图    
我个人是一个群放三个，随时备用,会长再也不用担心打不了公会战了,哦原来会长是我啊  
保1200公会招人，还没满嘤嘤嘤         
点个star让我知道有人在用才有动力更(   

本插件使用[GLWTPL(Good Luck With That Public License)](https://github.com/me-shaon/GLWTPL)开源，即： 
- 1.代码处于可用或不可用状态，没有第三种情况。  
- 2.版权所有© 每个人，除了作者  
- 3.在不导致作者被指责或承担责任的情况下，你可以做任何你想要做的事情。  
- 4.祝你好运  

# 已知问题  
没有问题！因为刚发，有问题赶紧提issue！不然我真的会忘了代码怎么写的  
暂不支持多gocq连一个hoshino，因为没试过，欢迎pr    


# 使用方法 

| 关键词     | 作用     |
| :-------------: | :-------------:|
|(被动)风控超过默认10次  | 切号！从自动切号列表按顺序切，原号进入已用名单
|(被动)账号已冻结       | 切号！从自动切号列表按顺序切，原号进入已用名单   
|切换账号 123456 |切换账号，被切的会被加入已用名单，不会进入自动切号列表
|激活账号 123456 |把账号从已用名单移除，重新加入自动切号列表
|账号列表  | 看看现在账号有啥        
|重载切号  |初始化everything

# 安装方法：  
1.复制整个文件夹放进modules，路径为\modules\txcnm\cg\_init_.py,填写config.yml,照格式添加    
2.pip install yaml  
3.bot设置加入txcnm  
安装实在是太简单了，很符合我对未来生活的想象，科技并带着偷懒。
