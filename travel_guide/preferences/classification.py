from sentence_transformers import SentenceTransformer, util
from travel_guide.preferences.schema import (
    get_all_value_candidates,
    get_empty_preferences
)


model = SentenceTransformer('all-MiniLM-L6-v2')


def retrieve_preferences(text: str, existing=None, threshold=0.6) -> dict:
    """
    使用语义匹配方式，从表达样例中检索最相似的偏好值。接替perferences classificaton llm 所有功能

    参数：
        text (str): 用户输入的整段偏好文本。
        existing (dict, optional): 当前已填写的偏好字典，包含所有字段（值为空表示尚未填写）。
                                   如果提供该参数，将只尝试补充尚未填写（值为""）的字段。
        threshold (float): 相似度阈值，超过该值才会视为有效匹配。

    返回：
        dict: 偏好字段到匹配值的字典（结构完整，仅更新空字段）。
    """
    preferences = existing.copy() if existing else get_empty_preferences()
    query_emb = model.encode(text, convert_to_tensor=True)
    schema = get_all_value_candidates()

    for field, value_map in schema.items():
        if preferences.get(field):
            continue  # 跳过已有值字段

        best_score = 0
        best_value = ""
        for val, example_list in value_map.items():
            for example in example_list:
                example_emb = model.encode(example, convert_to_tensor=True)
                score = float(util.cos_sim(query_emb, example_emb))
                if score > best_score:
                    best_score = score
                    best_value = val
        if best_score >= threshold:
            preferences[field] = best_value

    return preferences