"""
Lunchbox Data for DAR | RES group railway onboard dining service.
Stores structured multi-language lunchbox sets with portions and weights.
Languages supported: Kazakh (kk), Russian (ru), English (en).
"""
from typing import Optional


def normalize_lang(lang: Optional[str]) -> str:
    """Normalize language code to one of 'kk', 'ru', 'en'. Maps 'kz' -> 'kk'."""
    if not lang:
        return "ru"
    cleaned = lang.lower().strip()
    if cleaned in ("kk", "kz"):
        return "kk"
    if cleaned == "en":
        return "en"
    return "ru"


LUNCHBOXES_DATA = [
    {
        "id": 1,
        "number": 1,
        "sku": "LB-01",
        "weights": "200 / 100 / 30 / 60",
        "total_weight": 390,
        "title": {
            "ru": "Ланчбокс №1",
            "kk": "Ланчбокс №1",
            "en": "Lunchbox #1"
        },
        "description": {
            "ru": "Сбалансированный сытный обед с тушеной говядиной, пикантной морковью по-корейски, свежей выпечкой и мини-пирожным.",
            "kk": "Бұқтырылған сиыр еті, корейше сәбіз салаты, балғын тоқаш пен шағын тортшадан тұратын дәмді әрі теңгерімді тойымды жиынтық.",
            "en": "Balanced hearty lunchbox featuring braised beef with vegetables and rice, Korean-style carrot salad, pastry, and mini cake."
        },
        "items": [
            {
                "weight": 200,
                "type": "main",
                "name": {
                    "ru": "Говядина тушеная с овощами с рисом",
                    "kk": "Күріш қосылған көкөністі бұқтырылған сиыр еті",
                    "en": "Braised beef with vegetables and rice"
                }
            },
            {
                "weight": 100,
                "type": "salad",
                "name": {
                    "ru": "Салат морковь по-корейски",
                    "kk": "Корейше сәбіз салаты",
                    "en": "Korean-style carrot salad"
                }
            },
            {
                "weight": 30,
                "type": "pastry",
                "name": {
                    "ru": "Выпечка",
                    "kk": "Тоқаш",
                    "en": "Pastry"
                }
            },
            {
                "weight": 60,
                "type": "dessert",
                "name": {
                    "ru": "Мини-пирожное",
                    "kk": "Шағын тортша",
                    "en": "Mini cake"
                }
            }
        ]
    },
    {
        "id": 2,
        "number": 2,
        "sku": "LB-02",
        "weights": "200 / 100 / 30 / 60",
        "total_weight": 390,
        "title": {
            "ru": "Ланчбокс №2",
            "kk": "Ланчбокс №2",
            "en": "Lunchbox #2"
        },
        "description": {
            "ru": "Ароматное чахохбили из нежного куриного мяса с рисом, хрустящий свежий салат, аппетитная выпечка и сладкий десерт.",
            "kk": "Күріш қосылған тауық етінен чахохбили, балғын салат, тіл үйірер тоқаш пен шағын тортша қосылған теңгерімді ланчбокс.",
            "en": "Flavorful chicken chakhokhbili with rice, fresh garden salad, soft pastry, and a mini cake."
        },
        "items": [
            {
                "weight": 200,
                "type": "main",
                "name": {
                    "ru": "Чахохбили из курицы с рисом",
                    "kk": "Күріш қосылған тауық етінен чахохбили",
                    "en": "Chicken chakhokhbili with rice"
                }
            },
            {
                "weight": 100,
                "type": "salad",
                "name": {
                    "ru": "Свежий салат",
                    "kk": "Балғын салат",
                    "en": "Fresh salad"
                }
            },
            {
                "weight": 30,
                "type": "pastry",
                "name": {
                    "ru": "Выпечка",
                    "kk": "Тоқаш",
                    "en": "Pastry"
                }
            },
            {
                "weight": 60,
                "type": "dessert",
                "name": {
                    "ru": "Мини-пирожное",
                    "kk": "Шағын тортша",
                    "en": "Mini cake"
                }
            }
        ]
    },
    {
        "id": 3,
        "number": 3,
        "sku": "LB-03",
        "weights": "200 / 100 / 30 / 60",
        "total_weight": 390,
        "title": {
            "ru": "Ланчбокс №3",
            "kk": "Ланчбокс №3",
            "en": "Lunchbox #3"
        },
        "description": {
            "ru": "Классические макароны по-флотски с мясным фаршем, легкий салат из свежей капусты с огурцом, домашняя выпечка и мини-пирожное.",
            "kk": "Классикалық флотша макарон, қырыққабат пен қиярдан жасалған жеңіл салат, дәмді тоқаш және нәзік шағын тортшадан тұратын теңгерімді ланчбокс.",
            "en": "Classic navy-style pasta with minced meat, fresh cabbage and cucumber salad, homemade pastry, and a mini cake."
        },
        "items": [
            {
                "weight": 200,
                "type": "main",
                "name": {
                    "ru": "Макароны по-флотски",
                    "kk": "Флотша макарон",
                    "en": "Navy-style pasta"
                }
            },
            {
                "weight": 100,
                "type": "salad",
                "name": {
                    "ru": "Салат из капусты с огурцом",
                    "kk": "Қырыққабат пен қияр салаты",
                    "en": "Cabbage and cucumber salad"
                }
            },
            {
                "weight": 30,
                "type": "pastry",
                "name": {
                    "ru": "Выпечка",
                    "kk": "Тоқаш",
                    "en": "Pastry"
                }
            },
            {
                "weight": 60,
                "type": "dessert",
                "name": {
                    "ru": "Мини-пирожное",
                    "kk": "Шағын тортша",
                    "en": "Mini cake"
                }
            }
        ]
    }
]


def get_localized_lunchboxes(lang: str = "ru"):
    """
    Returns lunchboxes with text fields resolved to the chosen language.
    Supports 'kk', 'ru', 'en'.
    """
    norm_lang = normalize_lang(lang)
    unit = "г" if norm_lang == "kk" else ("g" if norm_lang == "en" else "гр")

    localized = []
    for lb in LUNCHBOXES_DATA:
        title = lb["title"].get(norm_lang) or lb["title"].get("ru")
        desc = lb["description"].get(norm_lang) or lb["description"].get("ru")
        items = []
        for it in lb["items"]:
            it_name = it["name"].get(norm_lang) or it["name"].get("ru")
            items.append({
                "weight": it["weight"],
                "type": it["type"],
                "name": it_name,
                "weight_str": f"{it['weight']} {unit}"
            })
        localized.append({
            "id": lb["id"],
            "number": lb["number"],
            "sku": lb["sku"],
            "weights": lb["weights"],
            "total_weight": lb["total_weight"],
            "unit": unit,
            "weights_str": f"{lb['weights']} {unit}",
            "total_weight_str": f"{lb['total_weight']} {unit}",
            "title": title,
            "description": desc,
            "items": items,
            "components": items,
        })
    return localized
