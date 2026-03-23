import asyncio
import logging
import pytz
import random
import re
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from chinese_calendar import is_workday

# ================= 配置日志 =================
logging.basicConfig(
    filename='telegram_msg.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    encoding='utf-8'
)
# ===========================================

# ================= 配置区域 =================
# 1. 请访问 https://my.telegram.org 获取 API_ID 和 API_HASH
# 请将下面的数字和字符串替换为你自己的真实数据
API_ID = 34650992  # 这里的 API_ID 必须是整数
API_HASH = 'c09d58fca51c08aed1cc3654299df35f'

# 2. 目标用户的用户名 (例如 '@username') 或手机号
# 注意：如果是第一次运行，脚本会提示你在终端输入手机号和验证码进行登录
TARGET_USER = '@julian_xzx'
CHECKIN_BOT = '@jike1024_bot'
# 3. 会话文件名称 (会自动生成 .session 文件保存登录状态)
SESSION_NAME = 'my_user_bot'
# ===========================================

# 初始化客户端
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# 全局变量，用于防止短时间内重复触发二次 checkin
last_checkin_time = datetime.min.replace(tzinfo=pytz.timezone('Asia/Shanghai'))
# 记录上一次发送的指令，用于二次确认时重发相同指令
last_sent_command = '/checkin' 

@client.on(events.NewMessage(from_users=TARGET_USER))
async def handle_new_message(event):
    """
    监听目标用户回复的消息
    """
    global last_checkin_time, last_sent_command
    try:
        sender = await event.get_sender()
        message_content = event.text
        # 获取发送者的显示名称，如果没有则使用 username
        sender_name = getattr(sender, 'first_name', '') or sender.username or 'Unknown'
        
        log_msg = f"收到来自 {sender_name} 的消息: {message_content}"
        # 获取当前时间（带时区）
        tz_cn = pytz.timezone('Asia/Shanghai')
        now_cn = datetime.now(tz_cn)
        
        print(f"\n[{now_cn.strftime('%Y-%m-%d %H:%M:%S')}] {log_msg}")
        logging.info(log_msg)
        
        # 自动回复数学题逻辑
        # 匹配模式：数字 空格? 运算符 空格? 数字
        # 例如: "12 + 34", "10-5", "计算 5 + 6"
        match = re.search(r'(\d+)\s*([\+\-\*\/])\s*(\d+)', message_content)
        if match:
            try:
                num1 = int(match.group(1))
                operator = match.group(2)
                num2 = int(match.group(3))
                
                result = 0
                if operator == '+':
                    result = num1 + num2
                elif operator == '-':
                    result = num1 - num2
                elif operator == '*':
                    result = num1 * num2
                elif operator == '/':
                    # 防止除以零
                    if num2 != 0:
                        result = num1 // num2
                    else:
                        result = 0
                
                log_math = f"检测到数学题: {num1} {operator} {num2} = {result}"
                print(f"[{datetime.now(tz_cn).strftime('%Y-%m-%d %H:%M:%S')}] {log_math}")
                logging.info(log_math)
                
                # 随机延迟 3-6 秒后回复，模拟人类思考
                await asyncio.sleep(random.randint(3, 6))
                
                await event.reply(str(result))
                
                log_reply = f"已自动回复计算结果: {result}"
                print(f"[{datetime.now(tz_cn).strftime('%Y-%m-%d %H:%M:%S')}] {log_reply}")
                logging.info(log_reply)
                
            except Exception as e:
                err_msg = f"计算或回复出错: {e}"
                print(err_msg)
                logging.error(err_msg)
        
        # 二次确认逻辑：如果收到“成功”，再次发送上次的指令
        if "成功" in message_content:
            # 5分钟冷却时间，防止死循环
            if (now_cn - last_checkin_time).total_seconds() > 300:
                log_success = f"检测到'成功'关键词，执行二次确认 {last_sent_command}..."
                print(f"[{datetime.now(tz_cn).strftime('%Y-%m-%d %H:%M:%S')}] {log_success}")
                logging.info(log_success)
                
                await asyncio.sleep(random.randint(2, 5))
                
                # 再次发送上次的指令
                await client.send_message(TARGET_USER, last_sent_command)
                
                # 更新时间戳
                last_checkin_time = now_cn
            else:
                log_skip = "检测到'成功'，但处于冷却时间内，跳过二次确认。"
                print(f"[{datetime.now(tz_cn).strftime('%Y-%m-%d %H:%M:%S')}] {log_skip}")
                
    except Exception as e:
        print(f"处理消息时出错: {e}")

async def schedule_checkin_tasks():
    """
    根据中国工作日和特定时间段发送消息
    """
    global last_sent_command
    print("定时任务已启动...")
    tz_cn = pytz.timezone('Asia/Shanghai')
    
    while True:
        # 获取当前时间（带时区）
        now = datetime.now(tz_cn)
        today = now.date()
        
        # 获取今天和明天的所有任务
        candidates = []
        
        # 定义获取单日任务的逻辑
        def get_tasks_for_date(d):
            daily_tasks = []
            base_dt = datetime.combine(d, datetime.min.time()).replace(tzinfo=tz_cn)
            
            is_sat = d.weekday() == 5
            run_today = False
            is_sat_schedule = False
            
            if is_sat:
                # 周六规则：如果周五（昨天）是工作日，或者周六本身是法定工作日，则运行
                yesterday = d - timedelta(days=1)
                if is_workday(yesterday) or is_workday(d):
                    run_today = True
                    is_sat_schedule = True
            else:
                # 非周六：如果是法定工作日则运行
                if is_workday(d):
                    run_today = True
            
            if run_today:
                if is_sat_schedule:
                    # 周六特殊时间表: 19:00 checkout, 无 22:00
                    points = [(9, '/checkin'), (14, '/checkin'), (19, '/checkout')]
                else:
                    # 平日时间表: 19:00 checkin, 22:00 checkout
                    points = [(9, '/checkin'), (14, '/checkin'), (19, '/checkin'), (22, '/checkout')]
                
                for h, msg in points:
                    # 基础时间
                    t = base_dt.replace(hour=h, minute=0, second=0, microsecond=0)
                    
                    # 添加随机延迟 (0 到 5 分钟)
                    # 为了保证同一个时间点每次计算出的随机数一致（避免循环中重复变动），
                    # 我们可以使用时间戳作为随机种子，或者在生成任务时一次性确定。
                    # 这里为了简单有效，我们在生成 daily_tasks 时直接加上随机秒数。
                    random_seconds = random.randint(0, 300)  # 0~300秒 即 0~5分钟
                    t += timedelta(seconds=random_seconds)
                    
                    daily_tasks.append((t, msg))
            
            # 按时间排序，防止随机后顺序错乱（虽然间隔很大一般不会）
            daily_tasks.sort(key=lambda x: x[0])
            return daily_tasks

        # 加载今天和明天的任务
        candidates.extend(get_tasks_for_date(today))
        candidates.extend(get_tasks_for_date(today + timedelta(days=1)))
        
        # 过滤掉已经过去的时间点
        future_tasks = [t for t in candidates if t[0] > now]
        
        if not future_tasks:
            # 如果明天的任务也没生成（例如连续放假），就休眠久一点再检查
            print("近期无任务，休眠 1 小时...")
            await asyncio.sleep(3600)
            continue
            
        # 获取下一个最近的任务
        target_time, message = future_tasks[0]
        
        wait_seconds = (target_time - now).total_seconds()
        print(f"距离下次发送还有 {int(wait_seconds)} 秒 (将在 {target_time.strftime('%Y-%m-%d %H:%M:%S')} 发送: {message})")
        
        # 等待直到目标时间
        await asyncio.sleep(wait_seconds)
        
        # 执行发送
        try:
            print(f"正在给 {TARGET_USER} 发送消息: {message}...")
            # 更新 last_sent_command，以便二次确认时使用
            last_sent_command = message
            
            await client.send_message(TARGET_USER, message)
            log_msg = f"定时消息发送成功: {message}"
            print(f"[{datetime.now(tz_cn).strftime('%Y-%m-%d %H:%M:%S')}] {log_msg}")
            logging.info(log_msg)
        except Exception as e:
            err_msg = f"消息发送失败: {e}"
            print(err_msg)
            logging.error(err_msg)
            
        # 发送完后，等待 60 秒，避免在同一分钟内重复触发
        await asyncio.sleep(60)

async def main():
    # 启动客户端
    print("正在启动 Telegram 客户端...")
    # start() 会处理登录流程，如果未登录会提示输入手机号和验证码
    await client.start()
    print("客户端登录成功！")
    
    # 创建并发运行的定时任务
    asyncio.create_task(schedule_checkin_tasks())
    
    # 保持程序运行以监听消息
    print(f"正在监听 {TARGET_USER} 的消息...")
    await client.run_until_disconnected()

if __name__ == '__main__':
    # 简单的检查
    if API_HASH == 'your_api_hash_here':
        print("错误: 请先打开脚本文件，填写你的 API_ID 和 API_HASH！")
    else:
        try:
            client.loop.run_until_complete(main())
        except KeyboardInterrupt:
            print("\n程序已停止。")