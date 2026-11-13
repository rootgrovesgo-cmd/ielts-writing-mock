#!/usr/bin/env python3
"""Write the student paper and teacher keys for Listening Set A."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER_PATH = ROOT / "prompts" / "listening_set_a.json"
KEYS_PATH = ROOT / "prompts" / "listening_keys.json"

WL1 = {"max_words": 1, "allow_number": True}
WL1_ONLY = {"max_words": 1, "allow_number": False}


def _existing_durations() -> dict[int, int]:
    if not PAPER_PATH.exists():
        return {}
    try:
        paper = json.loads(PAPER_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[int, int] = {}
    for section in paper.get("sections") or []:
        try:
            sid = int(section.get("id"))
            seconds = int((section.get("audio") or {}).get("duration_seconds") or 0)
        except (TypeError, ValueError):
            continue
        if seconds > 0:
            out[sid] = seconds
    return out


def _audio(sid: int, durations: dict[int, int]) -> dict:
    return {"file": f"section{sid}.mp3", "duration_seconds": int(durations.get(sid) or 0)}


def paper(durations: dict[int, int] | None = None) -> dict:
    durations = durations or {}
    return {
        "id": "set-a",
        "title": "Academic Listening Set A",
        "check_seconds": 120,
        "sections": [
            {
                "id": 1,
                "title": "Section 1",
                "context": "A conversation in which a woman asks a colleague for recommendations of independent bookshops.",
                "audio": _audio(1, durations),
                "groups": [
                    {
                        "id": "s1-table",
                        "from": 1,
                        "to": 10,
                        "type": "notes_table",
                        "heading": "Questions 1–10",
                        "instructions": [
                            "Complete the notes below.",
                            "Write ONE WORD AND/OR A NUMBER for each answer.",
                        ],
                        "word_limit": WL1,
                        "table": {
                            "title": "Bookshop recommendations",
                            "headers": [
                                "Name of bookshop",
                                "Location",
                                "Reason for recommendation",
                                "Other comments",
                            ],
                            "rows": [
                                [
                                    [["Ink & Timber"]],
                                    [["opposite the tram stop"]],
                                    [["specialist collection of ", {"q": 1}]],
                                    [
                                        ["can be noisy"],
                                        ["has a ", {"q": 2}, " that is good for sitting and reading"],
                                    ],
                                ],
                                [
                                    [["Harbour Folio"]],
                                    [["in the covered market"]],
                                    [["mostly ", {"q": 3}, " stock"]],
                                    [
                                        ["friendly staff"],
                                        ["will take a deposit to order a title"],
                                        ["limited selection of ", {"q": 4}, " for teenage customers"],
                                    ],
                                ],
                                [
                                    [["The ", {"q": 5}]],
                                    [["at the top of a ", {"q": 6}]],
                                    [
                                        ["well-known owner"],
                                        ["All the ", {"q": 7}, " are very good"],
                                    ],
                                    [
                                        ["Only uses ", {"q": 8}, " paper"],
                                        ["Membership: £", {"q": 9}],
                                        ["The rooms are probably ", {"q": 10}, " in size"],
                                    ],
                                ],
                            ],
                        },
                    }
                ],
            },
            {
                "id": 2,
                "title": "Section 2",
                "context": "A welcome talk by the leader of a community beekeeping workshop.",
                "audio": _audio(2, durations),
                "groups": [
                    {
                        "id": "s2-mcq",
                        "from": 11,
                        "to": 16,
                        "type": "mcq",
                        "heading": "Questions 11–16",
                        "instructions": ["Choose the correct letter, A, B or C."],
                        "items": [
                            {
                                "q": 11,
                                "stem": "The speaker says beekeeping differs from other outdoor activities because",
                                "options": {
                                    "A": "it can easily be fitted into a weekend",
                                    "B": "it involves working with a self-organising colony",
                                    "C": "the starter equipment is unusually cheap",
                                },
                            },
                            {
                                "q": 12,
                                "stem": "Inspectors sometimes identify a hive’s previous use from",
                                "options": {
                                    "A": "the colour of the paint",
                                    "B": "the material the hive is made from",
                                    "C": "marks left on the landing board",
                                },
                            },
                            {
                                "q": 13,
                                "stem": "Some people join the class because they want to",
                                "options": {
                                    "A": "sell honey at a local market",
                                    "B": "pass a hive on to their family",
                                    "C": "copy a neighbour who already keeps bees",
                                },
                            },
                            {
                                "q": 14,
                                "stem": "What does the speaker value most about being a beekeeper?",
                                "options": {
                                    "A": "the calming effect of inspecting a hive",
                                    "B": "the physical work of lifting the boxes",
                                    "C": "the messy and unpredictable nature of the activity",
                                },
                            },
                            {
                                "q": 15,
                                "stem": "Most of the visitors to the apiary",
                                "options": {
                                    "A": "come with a friend",
                                    "B": "are visiting for the first time",
                                    "C": "want to try advanced techniques immediately",
                                },
                            },
                            {
                                "q": 16,
                                "stem": "The speaker reminds visitors that they should",
                                "options": {
                                    "A": "remove jewellery and tie back long hair",
                                    "B": "learn how to light the smoker before the tour",
                                    "C": "put on a veil before leaving the bench area",
                                },
                            },
                        ],
                    },
                    {
                        "id": "s2-ct-1718",
                        "from": 17,
                        "to": 18,
                        "type": "choose_two",
                        "heading": "Questions 17 and 18",
                        "instructions": ["Choose TWO letters, A–E."],
                        "stem": "Which TWO things does the speaker explain about the smoker?",
                        "options": {
                            "A": "when the first version of it was invented",
                            "B": "what the smoke actually does to the bees",
                            "C": "where a spare smoker should be kept at home",
                            "D": "what some beekeepers use instead of a smoker",
                            "E": "how to repair a damaged bellows",
                        },
                    },
                    {
                        "id": "s2-ct-1920",
                        "from": 19,
                        "to": 20,
                        "type": "choose_two",
                        "heading": "Questions 19 and 20",
                        "instructions": ["Choose TWO letters, A–E."],
                        "stem": "Which TWO points does the speaker make about beekeeping tools?",
                        "options": {
                            "A": "Some have names that are difficult to remember.",
                            "B": "Some are surprisingly heavy to hold.",
                            "C": "Some are adapted from tools used in other trades.",
                            "D": "Some need to be cleaned after every visit to the apiary.",
                            "E": "Some are no longer being manufactured.",
                        },
                    },
                ],
            },
            {
                "id": 3,
                "title": "Section 3",
                "context": "Two university students discussing research for a presentation on academic burnout.",
                "audio": _audio(3, durations),
                "groups": [
                    {
                        "id": "s3-ct-2122",
                        "from": 21,
                        "to": 22,
                        "type": "choose_two",
                        "heading": "Questions 21 and 22",
                        "instructions": ["Choose TWO letters, A–E."],
                        "stem": "Which TWO things do the students both believe are responsible for the increase in academic burnout?",
                        "options": {
                            "A": "longer commuting times",
                            "B": "the growing use of social media",
                            "C": "a heavier assessment load",
                            "D": "a recent change in term dates",
                            "E": "greater financial pressure on students",
                        },
                    },
                    {
                        "id": "s3-ct-2324",
                        "from": 23,
                        "to": 24,
                        "type": "choose_two",
                        "heading": "Questions 23 and 24",
                        "instructions": ["Choose TWO letters, A–E."],
                        "stem": "Which TWO findings associated with burnout do the students agree are based on solid evidence?",
                        "options": {
                            "A": "It reduces short-term memory.",
                            "B": "It is a direct cause of depression.",
                            "C": "It is linked to higher drop-out rates.",
                            "D": "It permanently lowers academic grades.",
                            "E": "It makes group work impossible.",
                        },
                    },
                    {
                        "id": "s3-ct-2526",
                        "from": 25,
                        "to": 26,
                        "type": "choose_two",
                        "heading": "Questions 25 and 26",
                        "instructions": ["Choose TWO letters, A–E."],
                        "stem": "Which TWO opinions do both the students express about Merrow’s threshold model of burnout?",
                        "options": {
                            "A": "It has little practical relevance.",
                            "B": "It needs further investigation.",
                            "C": "It is misleading.",
                            "D": "It should be more widely accepted.",
                            "E": "It is difficult to understand.",
                        },
                    },
                    {
                        "id": "s3-mcq",
                        "from": 27,
                        "to": 30,
                        "type": "mcq",
                        "heading": "Questions 27–30",
                        "instructions": ["Choose the correct letter, A, B or C."],
                        "items": [
                            {
                                "q": 27,
                                "stem": "When comparing burnout to ordinary stress, the students",
                                "options": {
                                    "A": "doubt that a complete cure for burnout will ever exist",
                                    "B": "think the link between the two is overstated",
                                    "C": "express frustration that burnout is not taken seriously",
                                },
                            },
                            {
                                "q": 28,
                                "stem": "Why do the students decide to start their presentation with an example from their own experience?",
                                "options": {
                                    "A": "to show how severe burnout can become",
                                    "B": "so the audience will recognise the situation",
                                    "C": "to illustrate a difference between men and women",
                                },
                            },
                            {
                                "q": 29,
                                "stem": "The students agree that short walks are a good strategy for dealing with burnout because",
                                "options": {
                                    "A": "they help students generate new ideas",
                                    "B": "they interrupt the cycle before it builds",
                                    "C": "they are recommended in most study guides",
                                },
                            },
                            {
                                "q": 30,
                                "stem": "The students find it difficult to understand why working under pressure is considered to be",
                                "options": {
                                    "A": "enjoyable",
                                    "B": "necessary",
                                    "C": "similar to burnout",
                                },
                            },
                        ],
                    },
                ],
            },
            {
                "id": 4,
                "title": "Section 4",
                "context": "A lecture on reclaiming urban rooftops.",
                "audio": _audio(4, durations),
                "groups": [
                    {
                        "id": "s4-notes",
                        "from": 31,
                        "to": 40,
                        "type": "notes",
                        "heading": "Questions 31–40",
                        "instructions": [
                            "Complete the notes below.",
                            "Write ONE WORD ONLY for each answer.",
                        ],
                        "word_limit": WL1_ONLY,
                        "notes": {
                            "title": "Reclaiming urban rooftops",
                            "sections": [
                                {
                                    "heading": "Historical background",
                                    "items": [
                                        {
                                            "parts": [
                                                "Nineteenth-century roofs mainly held chimneys and water tanks",
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "Later problems often traced to the use of ",
                                                {"q": 31},
                                                " as waterproofing",
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "In 1974, a government survey declared the typical inner-city roof ",
                                                {"q": 32},
                                            ]
                                        },
                                    ],
                                },
                                {
                                    "heading": "Recent improvements",
                                    "items": [
                                        {
                                            "parts": [
                                                "An unexpected sighting on planted roofs: ",
                                                {"q": 33},
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "Old roof rooms converted into studios or ",
                                                {"q": 34},
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "Tampere has plans to:",
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "– build a rooftop ",
                                                {"q": 35},
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "– display ",
                                                {"q": 36},
                                                " projects",
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "Coimbra: ",
                                                {"q": 37},
                                                " are created on rooftops every summer",
                                            ]
                                        },
                                    ],
                                },
                                {
                                    "heading": "Practical possibilities",
                                    "items": [
                                        {
                                            "parts": [
                                                "A large number of city schools already have a rooftop ",
                                                {"q": 38},
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "Demand for fresh salad crops is increasing",
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "Instead of trucking produce from rural glasshouses, crops could be grown using soil beds and electric ",
                                                {"q": 39},
                                                ", or in future by ",
                                                {"q": 40},
                                            ]
                                        },
                                    ],
                                },
                            ],
                        },
                    }
                ],
            },
        ],
    }


def _q(answer, typ, explanation, alternatives=None, word_limit=None, pair=None):
    item = {"answer": answer, "type": typ, "explanation": explanation}
    if alternatives:
        item["alternatives"] = alternatives
    if word_limit:
        item["word_limit"] = word_limit
    if pair:
        item["pair"] = list(pair)
    return item


def keys() -> dict:
    return {
        "set_id": "set-a",
        "questions": {
            "1": _q(
                "poetry",
                "notes_table",
                "Fraser 承认位置方便，但明确说 that’s not necessarily why I’d recommend it。人们专程来是因为诗歌（poetry）收藏。不要填 location / tram / centre。",
                word_limit=WL1,
            ),
            "2": _q(
                "courtyard",
                "notes_table",
                "后部有 courtyard，适合坐着阅读。需要订位、能看到古城墙只是附加信息，不是空格要填的场所名词。不要填 wall 或 table。",
                word_limit=WL1,
            ),
            "3": _q(
                "academic",
                "notes_table",
                "Naomi 以为是二手书店；Fraser 说明那是店主以前工作的 Canal Row 旧店。他用确认问句后给出 Harbour Folio 的定位：academic 库存。不要填 second-hand。",
                word_limit=WL1,
            ),
            "4": _q(
                "comics",
                "notes_table",
                "Naomi 问起给十几岁侄女的读物。店里为青少年只保留有限的 comics，同时强调学术书并不短缺。不要填 academic 或 books，也不要理解成主库存不足。",
                alternatives=["comic"],
                word_limit=WL1,
            ),
            "5": _q(
                "Pellam",
                "notes_table",
                "店名 The Pellam，逐字母拼写为 P-E-L-L-A-M，并纠正人们常误写成 Pelham（多一个 H）。只接受此拼写（大小写不限）。",
                alternatives=["PELLAM"],
                word_limit=WL1,
            ),
            "6": _q(
                "staircase",
                "notes_table",
                "空格是 at the top of a 后面的名词。博物馆旁的咖啡馆是他人混淆的地点，不是书店位置。不要填 museum、café 或 arch。",
                alternatives=["stair"],
                word_limit=WL1,
            ),
            "7": _q(
                "reviews",
                "notes_table",
                "原文是 the reviews are excellent, from all the local papers and from customers online，对应笔记 All the reviews are very good。须用复数 reviews，与空格前后语法一致。不要填 staff、papers 或 owner。",
                word_limit=WL1,
            ),
            "8": _q(
                "handmade",
                "notes_table",
                "他们已停用廉价进口包装纸，改为只用本地作坊生产的 handmade paper。空格是 already printed 的 paper 前的形容词。不要填 imported 或 cheap。",
                alternatives=["hand-made", "hand made"],
                word_limit=WL1,
            ),
            "9": _q(
                "30",
                "notes_table",
                "年费本身是 thirty pounds / 30。十五镑是预留初版的押金，二十镑是学生优惠价，四十五镑是 Ink & Timber 的收费。题干已印英镑符号，填数字即可。",
                alternatives=["thirty", "30.00", "£30", "£30.00"],
                word_limit=WL1,
            ),
            "10": _q(
                "average",
                "notes_table",
                "两人原先都觉得房间太小；Fraser 用 I'd say / probably 修正为 average in size，并说价格还算合理。空格对应的是房间大小，不要填 small、tiny 或 fair。",
                word_limit=WL1,
            ),
            "11": _q(
                "B",
                "mcq",
                "与其他户外活动的真正区别是：你在与已经自我组织的蜂群合作。周末可安排、入门工具比预想便宜都被提及，但那不是蜜蜂养殖的独特之处。",
            ),
            "12": _q(
                "C",
                "mcq",
                "检查员是根据降落板（landing board）上的划痕/磨痕判断蜂箱过去的用途。油漆颜色、材质和基本形状都被当作不可靠的判断依据。",
            ),
            "13": _q(
                "B",
                "mcq",
                "卖蜂蜜、仿效邻居都是部分人的动机；演讲者强调相当一部分人是为了把蜂箱传给子女或孙辈，这才是题目问的 longer-term / legacy 动机。",
            ),
            "14": _q(
                "A",
                "mcq",
                "孩子喜欢messy、退休学员看重体力活动，但演讲者自己最珍视的是查看蜂箱时的平静感（calming）。注意 MOST / personally prize most。",
            ),
            "15": _q(
                "B",
                "mcq",
                "有人结伴而来，也有人急于尝试高级技法，但大多数来访者是第一次来的初学者。不要把少数情况当成 majority fact。",
            ),
            "16": _q(
                "C",
                "mcq",
                "珠宝和束发已在上周邮件里说明，点火器用法要等到上午晚些时候。现在立刻要做的是戴上身后长凳上的面罩（veil）。",
            ),
            "17": _q(
                "B",
                "choose_two",
                "17–18 题选 B 和 D，顺序不限。演讲者解释了烟雾的作用（掩盖蜜蜂的警报气味），以及有人改用水喷雾代替点火器。他只顺带提到发明很早，但没说发明时间（A 是陷阱）；说在家里放点火器不方便，但没有说明该放在哪里（C）；破损风箱的修理要以后再讲（E）。",
                pair=[17, 18],
            ),
            "18": _q(
                "D",
                "choose_two",
                "17–18 题选 B 和 D，顺序不限。演讲者解释了烟雾的作用（掩盖蜜蜂的警报气味），以及有人改用水喷雾代替点火器。他只顺带提到发明很早，但没说发明时间（A 是陷阱）；说在家里放点火器不方便，但没有说明该放在哪里（C）；破损风箱的修理要以后再讲（E）。",
                pair=[17, 18],
            ),
            "19": _q(
                "C",
                "choose_two",
                "19–20 题选 C 和 D，顺序不限。他明确指出有些工具是从油漆或抹灰等其他行业改来的，而且有些工具每次离开养蜂场后都需要清洁。名称只是被拿来开玩笑，他并不认为难记（A）；他也否认工具难拿或很重（B）；停产只是谣言，他予以否定（E）。",
                pair=[19, 20],
            ),
            "20": _q(
                "D",
                "choose_two",
                "19–20 题选 C 和 D，顺序不限。他明确指出有些工具是从油漆或抹灰等其他行业改来的，而且有些工具每次离开养蜂场后都需要清洁。名称只是被拿来开玩笑，他并不认为难记（A）；他也否认工具难拿或很重（B）；停产只是谣言，他予以否定（E）。",
                pair=[19, 20],
            ),
            "21": _q(
                "A",
                "choose_two",
                "21–22 题选 A 和 C，顺序不限。两人明确同意评估负担加重（I think you're right）以及通勤变长（That's true）。社交媒体被 Jonah 否定为主要原因；学期日期变动发生在多年前，无法解释近期上升；经济压力由 Lila 提出，但 Jonah 拒绝把它当作近期增加的原因，不能算双方共识。",
                pair=[21, 22],
            ),
            "22": _q(
                "C",
                "choose_two",
                "21–22 题选 A 和 C，顺序不限。两人明确同意评估负担加重（I think you're right）以及通勤变长（That's true）。社交媒体被 Jonah 否定为主要原因；学期日期变动发生在多年前，无法解释近期上升；经济压力由 Lila 提出，但 Jonah 拒绝把它当作近期增加的原因，不能算双方共识。",
                pair=[21, 22],
            ),
            "23": _q(
                "A",
                "choose_two",
                "23–24 题选 A 和 C，顺序不限。退学率有坚实的队列研究，双方接受；短期记忆一项在 Lila 引用 York 实验室 2021 年研究后两人同意证据充分。抑郁的定义含糊，不能说有直接因果关系；成绩永久下降的研究结果互相矛盾；小组活动无法进行只是 Lila 的个案，不能当作证据。",
                pair=[23, 24],
            ),
            "24": _q(
                "C",
                "choose_two",
                "23–24 题选 A 和 C，顺序不限。退学率有坚实的队列研究，双方接受；短期记忆一项在 Lila 引用 York 实验室 2021 年研究后两人同意证据充分。抑郁的定义含糊，不能说有直接因果关系；成绩永久下降的研究结果互相矛盾；小组活动无法进行只是 Lila 的个案，不能当作证据。",
                pair=[23, 24],
            ),
            "25": _q(
                "A",
                "choose_two",
                "25–26 题选 A 和 E，顺序不限。两人都说该模型难以理解，并且没什么实际用处。misleading 只是 Jonah 更进一步的看法，Lila 并不赞同；更广泛接受被 Lila 明确拒绝；需要进一步研究由 Lila 提起，Jonah 不愿把它作为两人的共同观点。",
                pair=[25, 26],
            ),
            "26": _q(
                "E",
                "choose_two",
                "25–26 题选 A 和 E，顺序不限。两人都说该模型难以理解，并且没什么实际用处。misleading 只是 Jonah 更进一步的看法，Lila 并不赞同；更广泛接受被 Lila 明确拒绝；需要进一步研究由 Lila 提起，Jonah 不愿把它作为两人的共同观点。",
                pair=[25, 26],
            ),
            "27": _q(
                "C",
                "mcq",
                "比较 burnout 与 ordinary stress 时，两人都表达frustrated：学校不当回事。Lila 明确说联系并非被夸大，也不讨论有没有cure。不要选 A 或 B。",
            ),
            "28": _q(
                "B",
                "mcq",
                "用自身例子开头是为了让听众 recognise the situation / see themselves in it。严重程度统计和性别差异可以稍后用，不是开场的理由。",
            ),
            "29": _q(
                "B",
                "mcq",
                "两人同意短时散步有效，是因为能 interrupt / break the cycle。有人赞散步能激发新想法，Jonah 否定这一点，因此 A 不是双方同意的理由。",
            ),
            "30": _q(
                "A",
                "mcq",
                "两人都不理解何以在压力下工作会被视为 enjoyable；他们自己并不喜欢压力，尽管研究认为它可能有益。题目问的是被视为怎样，不是 necessary 或 similar to burnout。",
            ),
            "31": _q(
                "bitumen",
                "notes",
                "后来诸多问题被追溯到二十世纪初把 bitumen 当作标准防水材料。chimneys、water tanks 是十九世纪屋顶上已有的东西，不是后来问题的成因。",
                word_limit=WL1_ONLY,
            ),
            "32": _q(
                "sterile",
                "notes",
                "1974 年政府调查的结论是典型内城屋顶被宣布为 sterile。不要填 dead、empty 或 industrial。",
                word_limit=WL1_ONLY,
            ),
            "33": _q(
                "lizards",
                "notes",
                "出乎意料出现在种植屋顶上的是 lizards。pigeons 和 fox 是调查人员原本预期会看到的，不是 unexpected sighting。",
                alternatives=["lizard"],
                word_limit=WL1_ONLY,
            ),
            "34": _q(
                "gyms",
                "notes",
                "旧屋顶房间被改成 studios 或 gyms。studios 已在笔记中给出，不要再填 studio。",
                alternatives=["gym"],
                word_limit=WL1_ONLY,
            ),
            "35": _q(
                "theatre",
                "notes",
                "Tampere 计划建造屋顶 theatre（露天小剧场）。不要填 auditorium 或 store。",
                alternatives=["theater"],
                word_limit=WL1_ONLY,
            ),
            "36": _q(
                "pilot",
                "notes",
                "该市还计划公开展示 pilot projects，供其他城区仿效。不要填 public、community 或 design。",
                word_limit=WL1_ONLY,
            ),
            "37": _q(
                "cinemas",
                "notes",
                "Coimbra 每年夏天在屋顶举办 cinemas。与 Tampere 的长期建设项目不同，这是夏季临时活动。语法上需要复数。",
                alternatives=["cinema"],
                word_limit=WL1_ONLY,
            ),
            "38": _q(
                "playground",
                "notes",
                "许多城市学校已经拥有屋顶 playground，这是现有做法，不是未来设想。不要填 garden 或 greenhouse。",
                alternatives=["playgrounds"],
                word_limit=WL1_ONLY,
            ),
            "39": _q(
                "lamps",
                "notes",
                "现在可用土壤苗床和 electric lamps 在屋顶种植；lamps 是当前已在室内园艺中使用的方式。不要填 glasshouses 或 trucks。",
                alternatives=["lights", "lamp", "light"],
                word_limit=WL1_ONLY,
            ),
            "40": _q(
                "robots",
                "notes",
                "未来则可由 robots（小型自动机械臂）完成种植与收获。这是 in future 的手段，不要与当前的 lamps 填反。",
                alternatives=["robot"],
                word_limit=WL1_ONLY,
            ),
        },
        "transcripts": {
            "1": "",
            "2": "",
            "3": "",
            "4": "",
        },
    }


def main() -> None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from listening_script import transcripts_for_keys

    durations = _existing_durations()
    data = keys()
    data["transcripts"] = transcripts_for_keys()
    PAPER_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAPER_PATH.write_text(json.dumps(paper(durations), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    KEYS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {PAPER_PATH}")
    print(f"Wrote {KEYS_PATH}")
    if durations:
        print("Preserved durations:", durations)


if __name__ == "__main__":
    main()
