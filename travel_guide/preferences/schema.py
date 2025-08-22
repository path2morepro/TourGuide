# travel_guide/preferences_schema.py
# 后续这部分的方案不知道怎么做，就先这样

# 一级分类描述（匹配模块使用）
PREFERENCE_FIELDS = {
    "pace": "旅行节奏相关偏好",
    "age_group": "旅客年龄段相关偏好",
    "mobility": "行动能力相关偏好",
    "language": "语言沟通相关偏好",
    "avoid": "需要避免的元素",
    "mood": "旅行氛围或体验偏好",
    "attraction": "景点选择相关偏好",
    "food": "饮食选择相关偏好",
    "accommodation": "住宿安排相关偏好",
    "transportation": "交通方式相关偏好"
}

# 候选值：每个字段下的具体子类值及语义解释（用于 embedding 匹配）
PREFERENCE_VALUE_CANDIDATES = {
    "pace": {
        "relaxed": ["我们想轻松一点，不要太赶", "每天行程少一些比较好", "能慢慢体验就行了"],
        "tight": ["希望行程安排紧凑一点", "多安排些活动", "尽量不要浪费时间", "希望一次将这里的景点都看完"],
        "free": ["我们想自由一些，不按固定计划走", "看当天心情安排活动", "临时决定去哪都可以", "随便"]
    },
    "accommodation": {
        "fixed": ["不想天天换地方住", "住宿最好固定一个地方", "希望住在同一个酒店"],
        "flexible": ["可以根据路线调整住宿", "愿意换不同地方住住看"],
        "quiet": ["希望住宿环境安静", "不要太吵的地方"],
        "convenient": ["住宿周围要方便买东西", "出门就有公交车最好"],
        "luxury": ["想住高档一点的酒店", "考虑有泳池或SPA的酒店"],
        "cheap": ["预算有限，住便宜点", "经济型酒店也可以"],
        "service": ["酒店服务要好", "最好有接送服务"]
    },
    "age_group": {
        "kids": ["我们带着小孩", "适合孩子玩的地方"],
        "aged": ["老人行动不便", "带着父母出行"],
        "students": ["学生党预算不多", "我们是学生一起出游"],
        "couples": ["情侣旅游", "适合二人世界"]
    },
    "mobility": {
        "weak": ["老人腿脚不方便", "需要轮椅通道", "推婴儿车"],
        "not_weak": ["走路没问题", "体力还可以"]
    },
    "language": {
        "barrier": ["不会外语", "希望有中文导游", "听不懂当地语言"],
        "average": ["会点英文", "可以简单交流"],
        "english_speaker": ["英文交流完全没问题", "能说流利英文"]
    },
    "avoid": {
        "museum": ["不喜欢看博物馆", "艺术馆太无聊了"],
        "heat": ["怕热", "不想去太热的地方"]
    },
    "mood": {
        "adventure": ["想刺激一点的体验", "有没有极限运动"],
        "relax": ["想放松一下", "主要是休息"],
        "romantic": ["想浪漫一点", "适合情侣的地方"],
        "cultural": ["体验下当地文化", "参观展览演出"],
        "spiritual": ["想找内心平静", "安静的自然环境"]
    },
    "attraction": {
        "nature": ["喜欢看自然风光", "想去山水类的景点"],
        "history": ["喜欢历史类景点", "古迹很有意思"],
        "culture": ["城市文化氛围重的地方", "喜欢艺术展、博物馆"],
        "entertainment": ["有没有好玩的地方", "想去游乐园或演出"]
    },
    "food": {
        "feature": ["想尝试当地特色美食", "想体验本地的饮食文化"],
        "no_interest": ["吃什么无所谓", "对吃的没特别要求", "怎么方便怎么来"],
        "hybrid": ["中餐西餐都可以", "希望饮食选择多样化"]
    },
    "transportation": {
        "public": ["希望坐地铁、公交", "公共交通方便最好"],
        "taxi": ["打车方便", "最好能随时打车"],
        "cheap": ["交通费便宜点", "能省则省"],
        "fast": ["希望交通快一点", "高铁飞机优先"]
    }
}

# 可选：默认结构初始化器
def get_empty_preferences():
    return {key: "" for key in PREFERENCE_FIELDS}

# 获取空字段列表
def get_missing_fields(preferences: dict) -> list:
    return [key for key in PREFERENCE_FIELDS if not preferences.get(key, "").strip()]

# 获取某个字段的描述（用于 embedding 一级匹配）
# 这个或许已经不需要了
def get_field_description(field):
    return PREFERENCE_FIELDS.get(field, "")

# 获取第一个未填写字段及其描述
def get_next_missing_field(preferences):
    for key in PREFERENCE_FIELDS:
        if not preferences.get(key, "").strip():
            return key, get_field_description(key)
    return None, None

# 获取字段列表
def get_all_fields():
    return list(PREFERENCE_FIELDS.keys())

# 获取指定字段的候选值表达样例（用于飞砖匹配）
def get_value_candidates(field):
    return PREFERENCE_VALUE_CANDIDATES.get(field, {})

# 获取new schema
def get_all_value_candidates():
    return PREFERENCE_VALUE_CANDIDATES


# 获取所有带候选表达字段
def get_fields_with_candidates():
    return list(PREFERENCE_VALUE_CANDIDATES.keys())

