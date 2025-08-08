import os
import asyncio
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
import app.services.rag as rag

# 初始化LLM模型
llm = init_chat_model(
    model="openai:qwen-plus",
    temperature=0.1,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.environ.get("aliQwen-api")
)

async def generate_answer_stream(user_input: str):
    """
    根据用户输入生成流式回答

    Args:
        user_input: 用户的问题

    Returns:
        生成器函数，用于流式返回回答
    """
    # 从检索器获取相关文档
    docs = rag.retriever.invoke(user_input)
    context = "\n".join([doc.page_content for doc in docs])

    # 构建提示词
    prompt = f"""
    你是一个乐于助人的FAQ智能体.
    你知道Python、AI、RAG等知识
    使用以下FAQ知识为基础来回答用户的问题：
    {context}
    如果用户问的问题和FAQ知识库中的问题不匹配或无关，请说："不知道，我的知识库中没有相关内容。"

    User question: {user_input}

    Answer:
    """

    # 构建消息
    messages = [
        SystemMessage(content="你叫FAQ智能体。"),
        HumanMessage(content=prompt)
    ]

    # 生成器函数
    async def answer_generator():
        try:
            for chunk in llm.stream(messages):
                yield chunk.content
                await asyncio.sleep(0)
        except Exception as e:
            yield f"\n❌ Error: {str(e)}"

    return answer_generator()
