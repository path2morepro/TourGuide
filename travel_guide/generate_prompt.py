from travel_guide.rag import llm
import re
import logging
import json
from travel_guide.preferences.schema import get_all_fields


def build_dialogue_prompt(trip_info: dict, user_message: str, history:str) -> str:
    """
    构造用于 LLM 多任务理解的 prompt，支持：
    - 收集用户偏好（append_preference）
    - 后续可拓展调用 tool_xxx（如查天气、订票等）
    
    参数：
    - trip_info: 当前用户行程基础信息（origin, destination, days 等）
    - user_message: 用户本轮输入

    返回：
    - prompt 字符串（供 LLM 理解任务并输出响应）
    """
    prompt = f"""
You are a travel assistant helping a user plan a trip.

User trip context:
- Departure: {trip_info['origin']}
- Destination: {trip_info['destination']}
- Duration: {trip_info['days']} days
- Budget: {trip_info.get('budget', 'N/A')}
- Date: {trip_info.get('date', 'N/A')}

Here is your historical conversation with the user:
{history}
User just said:
{user_message}

Instructions:
1. If the message reflects a user travel preference, return:
   append_preference("<summarized preference>")

2. If the message should trigger a functional action (e.g., tool_weather), output the corresponding tool call. (Not implemented yet, leave placeholder).

3. Otherwise, respond directly to the user as a helpful assistant.

Only output one of the following:
- a function call like: append_preference("...")
- reply in the language which user used
"""
    return prompt.strip()


def build_attraction_prompt(trip_info: dict) -> str:
    prefs = trip_info.get("preferences", {})
    lines = [
        f"景点：{prefs.get('attraction', '')}",
        f"饮食：{prefs.get('food', '')}",
        f"住宿：{prefs.get('accommodation', '')}",
        f"出行：{prefs.get('transportation', '')}",
        f"特殊需求：{prefs.get('special', '')}"
    ]
    content = "；".join([x for x in lines if x.strip().split('：')[1]])

    return f"""
你是一个旅行行程推荐助手。
请根据以下信息，推荐目的地内最适合用户的5个景点。
仅输出景点名称，每行一个，不要加任何说明或格式。

目的地：{trip_info.get("destination", "")}
偏好：{content}
""".strip()


