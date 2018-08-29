#!/usr/bin/env python3.6
# -*- coding: utf-8 -*-
'''
@author: Haffner2010
@contact: myprojtest@163.com
@Software: Pycharm + Python3.6
@OS:Windows 7 64 bit
@Site:https://www.jianshu.com/u/e031670b216b
@file: share.py
@time: 2018/8/20 20:03
@desc:
'''

import tushare as ts
import os
import time
import re
import datetime
from threading import Thread
from queue import Queue
from wxpy import *
from EmailAutoSend import *
# 邮件自动发送的代码https://github.com/allbluelai/AutoEmailSend

class Stock():
    '''
    获取股票的实时信息
    '''

    def __init__(self, q, stock_code):
        self.q = q
        self.stock_code = stock_code
        self._terminal = True #控制线程：这个stock我们希望外边能控制它的运行和停止，在stock类的入口，我们加入了一个_terminal变量

    def query_stock_real_price(self):
        df = ts.get_realtime_quotes(self.stock_code)
        df = df[['time', 'name','price']]
        return df


    def get_kline_data(self, ktype='ma5'):
        today = datetime.now().strftime('%Y-%m-%d')
        df = ts.get_hist_data(self.stock_code, start='2018-08-08', end=today)
        return (df[[ktype]])




    def start_run(self):
        while self._terminal:
            df= self.query_stock_real_price()
            # print(df)
            real_price = df['price'].values
            stock_name = df['name'].values
            self.q.put(dict(zip(stock_name, real_price)))
            # embed()
            time.sleep(3)


    def stop_run(self):
        self._terminal = False


# 登陆
bot = Bot(cache_path=True) # 缓存登陆信息
# bot = Bot()

bot.file_helper.send('hello world!')
# 获取好友
# dear = bot.friends().search('dear_friend')[0]
# 获取文件传输助手
file_helper = bot.file_helper


q = Queue()
stock_code=['601288','601328','601988','601398','601939']
stock=Stock(q,stock_code)
setting={
    '农业银行':[3.45,3.5],
    '交通银行':[5.4,5.7],
    '中国银行':[3.4,3.5],
    '工商银行':[5.3,5.4],
    '建设银行':[6.5,6.9]
} # 设置股票的期望买入下线和卖出上限

# watching stock real price every min
t = Thread(target=stock.start_run, args=())
t.start()
start_dt = datetime.datetime(datetime.date.today().year, datetime.date.today().month,
                    datetime.date.today().day, hour=9, minute=0, second=0) # 股市开始时间，用于开始查询股价的时间
stop_dt = datetime.datetime(datetime.date.today().year, datetime.date.today().month,
                   datetime.date.today().day, hour=15, minute=0, second=0) # 股市收市时间


# 消息接收监听器，通过接收文件传输助手的信息获取个人最新配置
@bot.register(chats=file_helper, except_self=False)
def print_others(message):
    # 输出监听到的消息
    print(message) # 此处的消息每次只能修改一只股票信息，对于实际应用来说已经足够
    msg_price = re.search('(.*?) : (.*?) \(Text\)', str(message)).group(2)
    print(msg_price)
    try:  # 格式code:high_pri,low_pri
        code, low_pri, high_pri = re.split('[:, ]', msg_price)
        print(code, low_pri, high_pri)
        name = ts.get_realtime_quotes(code)[['name']].values[0][0]
        setting.update({name:[float(low_pri),float(high_pri)]})
        print(setting)
    except:
        print('nothing')
    # return msg_price # 本来想通过return给外部函数接收以便修改setting的数据的，结果不知道如何使用，只能在register里面处理setting


while True:
    
    now_dt = datetime.datetime.now() # 当前股价查询时间
    if not start_dt < now_dt < stop_dt:
        title = f'Current Time {now_dt} is not between {start_dt} and {stop_dt},we will stop!'
        print(title)
        bot.file_helper.send(title)
        # 邮件信息
        subject = 'Stop Running!'
        # 纯文本邮件定义，邮件正文内容
        msg = MIMEText(title, 'plain', 'utf-8')
        # 定义发送人，接收人，以及描述信息（主题）
        msg['Subject'] = Header(subject, 'utf-8')
        MySMTP(myaccinfo, msg)
        stock.stop_run() # 不在开市范围内，停止执行
        break

    if not q.empty():
        cur_price_dict = q.get()
        print(cur_price_dict)
        print(f'Current stock price:{cur_price_dict}')        
        for item in cur_price_dict:
            cur_price = float(cur_price_dict[item])
            if cur_price > setting[item][1]:
                title = f'股票[{item}]：当前价格{cur_price}，高于max：{setting[item][1]}'
                print(title)
                bot.file_helper.send(title)
                # 邮件信息
                subject = '高阈值警告！'
                # 纯文本邮件定义，邮件正文内容
                msg = MIMEText(title, 'plain', 'utf-8')
                # 定义发送人，接收人，以及描述信息（主题）
                msg['Subject'] = Header(subject, 'utf-8')
                MySMTP(myaccinfo, msg)
                time.sleep(3)


            if cur_price < setting[item][0]:
                title = f'股票[{item}]：当前价格{cur_price}，低于min:{setting[item][0]}'
                print(title)
                bot.file_helper.send(title)
                # 邮件信息
                subject = '低阈值警告！'
                # 纯文本邮件定义，邮件正文内容
                msg = MIMEText(title, 'plain', 'utf-8')
                # 定义发送人，接收人，以及描述信息（主题）
                msg['Subject'] = Header(subject, 'utf-8')
                MySMTP(myaccinfo, msg)
                time.sleep(3)
t.join()
# embed()
