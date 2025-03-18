from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *  # 导入事件类
from pkg.platform.types import Plain  # 导入消息类型
import re
import logging  # 添加 logging 模块
import asyncio
import yaml
import os
from collections import defaultdict

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 注册插件
@register(
    name="SegmentPlugin",  # 英文名
    description="模拟人类打字习惯的消息分段发送插件", # 中文描述
    version="0.1",
    author="ablz"
)
class MyPlugin(BasePlugin):

    # 插件加载时触发
    def __init__(self, host: APIHost):
        self.typing_locks = defaultdict(asyncio.Lock)  # 每个对话的打字锁
        
        # 加载配置文件
        config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                settings = config.get('typing_settings', {})
                self.char_delay = settings.get('char_delay', 0.1)  # 每个字符的延迟
                self.segment_pause = settings.get('segment_pause', 0.5)  # 段落间停顿
                self.max_split_length = settings.get('max_split_length', 50)  # 最大分段长度
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            # 使用默认值
            self.char_delay = 0.1
            self.segment_pause = 0.5
            self.max_split_length = 50

    # 异步初始化
    async def initialize(self):
        pass

    def split_text(self, text: str) -> list:
        # 先处理括号内的内容
        segments = []
        current = ""
        in_parentheses = False
        
        # 需要删除的标点符号（包括冒号）
        skip_punctuation = []
        # 作为分段标记的标点符号
        split_punctuation = ["？", "！", "?", "!", "~", "〜"]
        
        for i, char in enumerate(text):
            if char == '(':
                in_parentheses = True
                if current.strip():
                    segments.append(current.strip())
                current = char
            elif char == ')':
                in_parentheses = False
                current += char
                segments.append(current.strip())
                current = ""
            elif char in skip_punctuation and not in_parentheses:
                continue
            else:
                current += char
                # 如果不在括号内且遇到分隔符，进行分段
                if not in_parentheses and char in split_punctuation:
                    segments.append(current.strip())
                    current = ""
        
        # 处理最后剩余的文本
        if current.strip():
            segments.append(current.strip())
        
        return [seg for seg in segments if seg.strip()]

    async def get_chat_lock(self, chat_type: str, chat_id: str) -> asyncio.Lock:
        """获取对话的锁"""
        lock_key = f"{chat_type}_{chat_id}"
        return self.typing_locks[lock_key]

    async def simulate_typing(self, ctx: EventContext, chat_type: str, chat_id: str, text: str):
        """模拟打字效果的延时"""
        # 获取此对话的锁
        lock = await self.get_chat_lock(chat_type, chat_id)
        
        # 等待获取锁
        async with lock:
            # 根据文本长度计算延时
            typing_delay = len(text) * self.char_delay
            # 发送完整消息
            await ctx.send_message(chat_type, chat_id, [Plain(text)])
            # 等待打字延时
            await asyncio.sleep(typing_delay)

    # 处理大模型的回复
    @handler(NormalMessageResponded)
    async def normal_message_responded(self, ctx: EventContext):
        chat_type = ctx.event.launcher_type
        chat_id = ctx.event.launcher_id if chat_type == "group" else ctx.event.sender_id
        
        # 获取大模型的回复文本
        response_text = ctx.event.response_text
        
        # 获取此对话的锁
        lock = await self.get_chat_lock(chat_type, chat_id)
        
        # 等待获取锁
        async with lock:
            # 如果文本长度超过最大分段长度，直接发送不分段
            if len(response_text) > self.max_split_length:
                logger.info(f"[分段发送] 文本长度({len(response_text)})超过最大限制({self.max_split_length})，将不进行分段")
                # 模拟整体打字延时并发送
                await self.simulate_typing(ctx, chat_type, chat_id, response_text)
                return
            
            # 分割文本
            parts = self.split_text(response_text)
            
            if parts:
                logger.info(f"[分段发送] {chat_type} {chat_id} 的消息将被分为 {len(parts)} 段发送")
                
                # 阻止默认的回复行为
                ctx.prevent_default()
                
                # 逐段发送消息
                for i, part in enumerate(parts, 1):
                    logger.info(f"[分段发送] 正在发送第 {i}/{len(parts)} 段: {part}")
                    # 模拟打字延时并发送
                    typing_delay = len(part) * self.char_delay
                    await ctx.send_message(chat_type, chat_id, [Plain(part)])
                    await asyncio.sleep(typing_delay)
                    
                    # 如果不是最后一段，添加段落间停顿
                    if i < len(parts):
                        await asyncio.sleep(self.segment_pause)

    # 插件卸载时触发
    def __del__(self):
        pass
