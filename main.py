# coding:utf-8
from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost
import re
from . import util

# 注册插件
@register(name="RemoveTagsAndSegment", description="适用于DeepSeekR1的去标签及分段插件", version="0.1", author="ablz")
class URLMaskerPlugin(Plugin):

    # 插件加载时触发
    def __init__(self, plugin_host: PluginHost):
        pass

    @handler(PromptPreProcessing)
    async def _(self, ctx: EventContext):
        if len(ctx.event.prompt) != 0:
            for promptindex, promptcontent in enumerate(ctx.event.prompt):
                if promptindex % 2 != 0:
                    ctx.event.prompt[promptindex].content = re.sub(r'<think>[\s\S]*?<\/think>\n\n', '', promptcontent.content)

    @on(NormalMessageResponded)
    def group_normal_message_received(self, event: EventContext, ​**kwargs):
        msg = kwargs['response_text']
        ret = util.removethink(msg)

        # 将 ret 分段，每段最长 1024 个字节
        ret_segments = [ret[i:i + 1024] for i in range(0, len(ret), 1024)]

        # 添加分段后的回复
        event.add_return('reply', ret_segments)

    # 插件卸载时触发
    def __del__(self):
        pass
