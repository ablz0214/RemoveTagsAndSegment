# coding:utf-8
from pkg.plugin.context import register, handler, llm_func, BasePlugin, APIHost, EventContext
from pkg.plugin.events import *
from pkg.plugin.models import *
from pkg.plugin.host import EventContext, PluginHost
import re
from . import util

# 注册插件
@register(name="DeepSeekR1nothink--update", description="remove think info for DeepSeekR1 model", version="0.1", author="abu")
class URLMaskerPlugin(Plugin):

    # 插件加载时触发
    # plugin_host (pkg.plugin.host.PluginHost) 提供了与主程序交互的一些方法，详细请查看其源码
    def __init__(self, plugin_host: PluginHost):
        pass
        
    @handler(PromptPreProcessing)
    async def _(self, ctx: EventContext):
        if len(ctx.event.prompt) != 0:
            for promptindex,promptcontent in enumerate(ctx.event.prompt):
                if promptindex % 2 != 0:
                    ctx.event.prompt[promptindex].content = re.sub(r'<think>[\s\S]*?<\/think>\n\n', '', promptcontent.content)

    @on(NormalMessageResponded)
    def group_normal_message_received(self, event: EventContext, **kwargs):
        msg = kwargs['response_text']
        ret = util.removethink(msg)
        event.add_return('reply', ret)

    # 插件卸载时触发
    def __del__(self):
        pass
