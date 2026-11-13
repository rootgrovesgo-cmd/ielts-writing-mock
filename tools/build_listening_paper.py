#!/usr/bin/env python3
"""Write the student paper and teacher keys for Listening Set A."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER_PATH = ROOT / "prompts" / "listening_set_a.json"
KEYS_PATH = ROOT / "prompts" / "listening_keys.json"

MAP_SVG = """<svg viewBox="0 0 720 540" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Plan of Saltmarsh Coastal Visitor Centre">
  <rect width="720" height="540" fill="#f3f0ea"/>
  <rect x="16" y="16" width="688" height="508" fill="#eef3f1" stroke="#c8c2b8" stroke-width="2"/>
  <!-- Lagoon -->
  <ellipse cx="400" cy="92" rx="260" ry="78" fill="#c9dbe3" stroke="#7d9aa6" stroke-width="2"/>
  <text x="400" y="86" text-anchor="middle" font-size="14" font-weight="700" fill="#3f3c3a">Lagoon</text>
  <!-- Spit / lookout F -->
  <path d="M430 40 L560 28 L575 70 L510 86 Z" fill="#d9d3c6" stroke="#9a9286" stroke-width="1.5"/>
  <!-- Boardwalk (labelled) -->
  <rect x="250" y="130" width="230" height="10" fill="#b89b6a"/>
  <text x="365" y="122" text-anchor="middle" font-size="11" fill="#5c564e">Boardwalk</text>
  <!-- Main building -->
  <rect x="300" y="260" width="150" height="110" fill="#dfe6ea" stroke="#5c6b73" stroke-width="2"/>
  <text x="375" y="318" text-anchor="middle" font-size="13" font-weight="700" fill="#3f3c3a">Main</text>
  <text x="375" y="336" text-anchor="middle" font-size="13" font-weight="700" fill="#3f3c3a">building</text>
  <!-- Cafe A, east of main -->
  <rect x="470" y="280" width="90" height="70" fill="#efe6d6" stroke="#8a7a5c" stroke-width="2"/>
  <!-- Exhibition hall B, north of main -->
  <rect x="310" y="190" width="130" height="58" fill="#e4e0d6" stroke="#5c6b73" stroke-width="2"/>
  <!-- Bird hide C, NE lagoon -->
  <rect x="575" y="115" width="70" height="40" fill="#d5e0d4" stroke="#5d6f5e" stroke-width="2"/>
  <!-- Picnic lawn D, west -->
  <ellipse cx="170" cy="250" rx="80" ry="55" fill="#d5e4c9" stroke="#7a9268" stroke-width="2"/>
  <!-- Boat shed E, east shore -->
  <rect x="600" y="210" width="72" height="48" fill="#e8d7c4" stroke="#8a6d52" stroke-width="2"/>
  <!-- Play area, prelabelled NW -->
  <rect x="70" y="150" width="100" height="55" fill="#efe3c8" stroke="#a08952" stroke-width="1.5"/>
  <text x="120" y="182" text-anchor="middle" font-size="11" font-weight="700" fill="#3f3c3a">Play area</text>
  <!-- Car park SW -->
  <rect x="60" y="390" width="150" height="90" fill="#d8d4cf" stroke="#8a847c" stroke-width="2" stroke-dasharray="6 4"/>
  <text x="135" y="440" text-anchor="middle" font-size="13" font-weight="700" fill="#3f3c3a">Car park</text>
  <!-- Entrance S -->
  <path d="M360 430 L375 510 L345 510 Z" fill="#c5c0b8" stroke="#8a847c"/>
  <text x="375" y="528" text-anchor="middle" font-size="12" font-weight="700" fill="#3f3c3a">Entrance</text>
  <!-- First aid near entrance, prelabelled -->
  <rect x="410" y="430" width="70" height="36" fill="#f3e0e0" stroke="#a66a6a" stroke-width="1.5"/>
  <text x="445" y="452" text-anchor="middle" font-size="10" font-weight="700" fill="#3f3c3a">First aid</text>
  <!-- Path lines -->
  <path d="M360 430 L375 370 L375 260" fill="none" stroke="#b7b1a8" stroke-width="8"/>
  <path d="M375 310 L470 310" fill="none" stroke="#b7b1a8" stroke-width="6"/>
  <path d="M375 220 L375 140" fill="none" stroke="#b7b1a8" stroke-width="6"/>
  <path d="M170 300 L300 310" fill="none" stroke="#b7b1a8" stroke-width="6"/>
  <path d="M150 390 L150 310 L170 280" fill="none" stroke="#b7b1a8" stroke-width="6"/>
  <path d="M450 220 L620 230" fill="none" stroke="#b7b1a8" stroke-width="6"/>
  <path d="M600 150 L610 210" fill="none" stroke="#b7b1a8" stroke-width="5"/>
  <!-- Letter markers -->
  <g font-family="Georgia, serif" font-size="16" font-weight="700" text-anchor="middle">
    <circle cx="515" cy="315" r="14" fill="#fff" stroke="#3f3c3a" stroke-width="2"/>
    <text x="515" y="321" fill="#3f3c3a">A</text>
    <circle cx="375" cy="219" r="14" fill="#fff" stroke="#3f3c3a" stroke-width="2"/>
    <text x="375" y="225" fill="#3f3c3a">B</text>
    <circle cx="610" cy="135" r="14" fill="#fff" stroke="#3f3c3a" stroke-width="2"/>
    <text x="610" y="141" fill="#3f3c3a">C</text>
    <circle cx="170" cy="250" r="14" fill="#fff" stroke="#3f3c3a" stroke-width="2"/>
    <text x="170" y="256" fill="#3f3c3a">D</text>
    <circle cx="636" cy="234" r="14" fill="#fff" stroke="#3f3c3a" stroke-width="2"/>
    <text x="636" y="240" fill="#3f3c3a">E</text>
    <circle cx="545" cy="48" r="14" fill="#fff" stroke="#3f3c3a" stroke-width="2"/>
    <text x="545" y="54" fill="#3f3c3a">F</text>
  </g>
  <text x="360" y="36" text-anchor="middle" font-size="13" font-weight="700" fill="#3f3c3a">Saltmarsh Coastal Visitor Centre</text>
</svg>"""


def paper() -> dict:
    return {
        "id": "set-a",
        "title": "Academic Listening Set A",
        "check_seconds": 120,
        "sections": [
            {
                "id": 1,
                "title": "Section 1",
                "context": "A telephone conversation about booking a weekend pottery workshop at a community arts centre.",
                "audio": {"file": "section1.mp3", "duration_seconds": 0},
                "groups": [
                    {
                        "id": "s1-form",
                        "from": 1,
                        "to": 8,
                        "type": "form",
                        "heading": "Questions 1–8",
                        "instructions": [
                            "Complete the form below.",
                            "Write NO MORE THAN TWO WORDS AND/OR A NUMBER for each answer.",
                        ],
                        "word_limit": {"max_words": 2, "allow_number": True},
                        "form_title": "Weekend pottery workshop — booking form",
                        "rows": [
                            {"label": "Surname", "q": 1, "hint": "please spell"},
                            {"label": "Contact number", "q": 2},
                            {"label": "Workshop date", "q": 3},
                            {"label": "Start time", "q": 4},
                            {"label": "Type of class", "q": 5},
                            {"label": "Fee payable", "prefix": "£", "q": 6},
                            {"label": "Please bring", "q": 7},
                            {"label": "How she heard about the centre", "q": 8},
                        ],
                    },
                    {
                        "id": "s1-mcq",
                        "from": 9,
                        "to": 10,
                        "type": "mcq",
                        "heading": "Questions 9–10",
                        "instructions": ["Choose the correct letter, A, B or C."],
                        "items": [
                            {
                                "q": 9,
                                "stem": "Where should Harriet park on Saturday?",
                                "options": {
                                    "A": "On Maple Street, which is free after 1 p.m.",
                                    "B": "In the centre’s own paid car park",
                                    "C": "In the supermarket car park across the road",
                                },
                            },
                            {
                                "q": 10,
                                "stem": "Why does Harriet want to take the workshop?",
                                "options": {
                                    "A": "To make a birthday gift for her sister",
                                    "B": "To start selling her own pottery",
                                    "C": "To see if she would enjoy a regular evening class",
                                },
                            },
                        ],
                    },
                ],
            },
            {
                "id": 2,
                "title": "Section 2",
                "context": "A welcome talk for visitors at the newly opened Saltmarsh Coastal Visitor Centre.",
                "audio": {"file": "section2.mp3", "duration_seconds": 0},
                "groups": [
                    {
                        "id": "s2-map",
                        "from": 11,
                        "to": 16,
                        "type": "map",
                        "heading": "Questions 11–16",
                        "instructions": [
                            "Label the plan below.",
                            "Choose the correct letter, A–F, for each place.",
                        ],
                        "map": {
                            "title": "Saltmarsh Coastal Visitor Centre",
                            "svg": MAP_SVG,
                        },
                        "items": [
                            {"q": 11, "stem": "Café"},
                            {"q": 12, "stem": "Exhibition hall"},
                            {"q": 13, "stem": "Bird hide"},
                            {"q": 14, "stem": "Picnic lawn"},
                            {"q": 15, "stem": "Boat shed"},
                            {"q": 16, "stem": "Lookout tower"},
                        ],
                        "options": ["A", "B", "C", "D", "E", "F"],
                    },
                    {
                        "id": "s2-matching",
                        "from": 17,
                        "to": 20,
                        "type": "matching",
                        "heading": "Questions 17–20",
                        "instructions": [
                            "What information is given about each of the following activities?",
                            "Choose the correct letter, A–F.",
                            "NB You may use any letter more than once.",
                        ],
                        "legend": [
                            {"key": "A", "text": "must be booked in advance"},
                            {"key": "B", "text": "available at weekends only"},
                            {"key": "C", "text": "free with the admission ticket"},
                            {"key": "D", "text": "runs in July and August only"},
                            {"key": "E", "text": "cancelled for this season"},
                            {"key": "F", "text": "restricted to centre members"},
                        ],
                        "items": [
                            {"q": 17, "stem": "Guided beach walks"},
                            {"q": 18, "stem": "Kayak hire"},
                            {"q": 19, "stem": "Telescope loans"},
                            {"q": 20, "stem": "Evening talks"},
                        ],
                    },
                ],
            },
            {
                "id": 3,
                "title": "Section 3",
                "context": "A tutor and three students discussing a research project on food waste in a university cafeteria.",
                "audio": {"file": "section3.mp3", "duration_seconds": 0},
                "groups": [
                    {
                        "id": "s3-mcq",
                        "from": 21,
                        "to": 26,
                        "type": "mcq",
                        "heading": "Questions 21–26",
                        "instructions": ["Choose the correct letter, A, B or C."],
                        "items": [
                            {
                                "q": 21,
                                "stem": "The main weakness of last year’s data was that they",
                                "options": {
                                    "A": "covered only a two-week period",
                                    "B": "were collected at lunchtime only",
                                    "C": "were damaged when a computer failed",
                                },
                            },
                            {
                                "q": 22,
                                "stem": "The group decides to measure",
                                "options": {
                                    "A": "the weight of leftovers left on plates",
                                    "B": "the amount of food that is never served",
                                    "C": "the number of meals students refuse",
                                },
                            },
                            {
                                "q": 23,
                                "stem": "Dr Brennan says the student interviews should",
                                "options": {
                                    "A": "be carried out in the cafeteria queue",
                                    "B": "include at least twenty questions",
                                    "C": "last no more than ten minutes",
                                },
                            },
                            {
                                "q": 24,
                                "stem": "Jade agrees to",
                                "options": {
                                    "A": "write the questionnaire",
                                    "B": "design the project poster",
                                    "C": "contact the kitchen manager",
                                },
                            },
                            {
                                "q": 25,
                                "stem": "They will present their findings",
                                "options": {
                                    "A": "at a departmental seminar",
                                    "B": "in a journal for students",
                                    "C": "at the campus sustainability fair",
                                },
                            },
                            {
                                "q": 26,
                                "stem": "Their greatest remaining concern is",
                                "options": {
                                    "A": "whether the kitchen staff will cooperate",
                                    "B": "whether they can borrow weighing scales",
                                    "C": "whether enough students will take part",
                                },
                            },
                        ],
                    },
                    {
                        "id": "s3-matching",
                        "from": 27,
                        "to": 30,
                        "type": "matching",
                        "heading": "Questions 27–30",
                        "instructions": [
                            "Who will do each of the following tasks?",
                            "Choose the correct letter, A, B or C.",
                        ],
                        "legend": [
                            {"key": "A", "text": "Jade"},
                            {"key": "B", "text": "Tomás"},
                            {"key": "C", "text": "Aisha"},
                        ],
                        "items": [
                            {"q": 27, "stem": "Write the literature review"},
                            {"q": 28, "stem": "Complete the ethics form"},
                            {"q": 29, "stem": "Run the pilot study"},
                            {"q": 30, "stem": "Book the meeting room"},
                        ],
                    },
                ],
            },
            {
                "id": 4,
                "title": "Section 4",
                "context": "A lecture on the Fenmere Levels peatland restoration project.",
                "audio": {"file": "section4.mp3", "duration_seconds": 0},
                "groups": [
                    {
                        "id": "s4-notes",
                        "from": 31,
                        "to": 40,
                        "type": "notes",
                        "heading": "Questions 31–40",
                        "instructions": [
                            "Complete the notes below.",
                            "Write NO MORE THAN TWO WORDS AND/OR A NUMBER for each answer.",
                        ],
                        "word_limit": {"max_words": 2, "allow_number": True},
                        "notes": {
                            "title": "The Fenmere Levels restoration",
                            "sections": [
                                {
                                    "heading": "Background",
                                    "items": [
                                        {
                                            "parts": [
                                                "Peat began to dry after nineteenth-century ",
                                                {"q": 31},
                                                " were constructed.",
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "Dried peat releases ",
                                                {"q": 32},
                                                " into the air.",
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "Shrinking ground has also damaged local ",
                                                {"q": 33},
                                                ".",
                                            ]
                                        },
                                    ],
                                },
                                {
                                    "heading": "The project",
                                    "items": [
                                        {
                                            "parts": [
                                                "Pumps were switched off in ",
                                                {"q": 34},
                                                ".",
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "Water levels are now controlled by ",
                                                {"q": 35},
                                                ".",
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "Work had to pause because of nesting ",
                                                {"q": 36},
                                                ".",
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "Farmers are compensated with a crop of ",
                                                {"q": 37},
                                                ".",
                                            ]
                                        },
                                    ],
                                },
                                {
                                    "heading": "Results and next steps",
                                    "items": [
                                        {
                                            "parts": [
                                                "An unexpected species to return: ",
                                                {"q": 38},
                                                ".",
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "Researchers are now measuring ",
                                                {"q": 39},
                                                " emissions.",
                                            ]
                                        },
                                        {
                                            "parts": [
                                                "A planned visitor facility: a ",
                                                {"q": 40},
                                                ".",
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


def _q(answer, typ, explanation, alternatives=None, word_limit=None):
    item = {"answer": answer, "type": typ, "explanation": explanation}
    if alternatives:
        item["alternatives"] = alternatives
    if word_limit:
        item["word_limit"] = word_limit
    return item


WL2 = {"max_words": 2, "allow_number": True}


def keys() -> dict:
    return {
        "set_id": "set-a",
        "questions": {
            "1": _q(
                "KERRIDGE",
                "form",
                "Harriet 先说成 Carridge，随即更正并拼写 K-E-R-R-I-D-G-E。不要填 Carridge 或 Harriet。",
                alternatives=["Kerridge"],
                word_limit=WL2,
            ),
            "2": _q(
                "07754 629183",
                "form",
                "她先报 07754 629813，随即更正为 07754 629183。后四位是 6183 的干扰不可用。",
                alternatives=["07754629183", "07754-629183", "07754 629 183"],
                word_limit=WL2,
            ),
            "3": _q(
                "18 May",
                "form",
                "她原想订 11 May，但 Marcus 说那一期已满，改订 18 May。不要填 11 May 或 25 May（候补日期）。",
                alternatives=["18th May", "May 18", "May 18th", "18 May"],
                word_limit=WL2,
            ),
            "4": _q(
                "2.15",
                "form",
                "宣传是 2 o’clock，但 Marcus 说明实际从 2.15 开始，以便先做安全须知。不要填 2.00 或 2 o’clock。",
                alternatives=["2:15", "14.15", "14:15", "2.15 pm", "2:15 pm", "2.15pm", "2:15pm"],
                word_limit=WL2,
            ),
            "5": _q(
                "wheel throwing",
                "form",
                "工作日才有 hand-building；她要订的周六课是 wheel throwing。不要填 hand-building 或 pottery。",
                alternatives=["wheel-throwing"],
                word_limit=WL2,
            ),
            "6": _q(
                "37.50",
                "form",
                "标准费用是 £37.50。优惠价 £29 仅给学生和六十岁以上人士，她不符合。不要填 29 或 45（材料押金）。",
                alternatives=["£37.50", "37.50 pounds", "£37.50 pounds"],
                word_limit=WL2,
            ),
            "7": _q(
                "old shirt",
                "form",
                "中心提供围裙和粘土，不要自带粘土。Marcus 建议带一件 old shirt 以免溅到衣服。不要填 apron 或 clay。超过两个词（如 an old shirt）按词数限制判错。",
                word_limit=WL2,
            ),
            "8": _q(
                "library poster",
                "form",
                "她说朋友提起过网站，但她实际是在图书馆海报上看到课程。不要填 website 或 friend。",
                alternatives=["library posters"],
                word_limit=WL2,
            ),
            "9": _q(
                "A",
                "mcq",
                "Marcus 先提到中心收费停车场，随后说明周六下午 1 点后 Maple Street 路边免费，并建议她把车停在那里。超市停车场只给顾客用。故选 A。",
            ),
            "10": _q(
                "C",
                "mcq",
                "姐姐喜欢陶艺只是闲聊；她明确说想先试一次，再决定要不要参加周二晚的常规课。不是为了做生日礼物或开店。故选 C。",
            ),
            "11": _q("A", "map", "咖啡馆紧挨主楼东侧，对应图上 A。不要与主楼内的咨询台混淆。"),
            "12": _q("B", "map", "展览厅在主楼正北、通往木栈道的路上，对应 B。"),
            "13": _q("C", "map", "观鸟屋在泻湖北岸东端，对应 C。不要把北面沙嘴上的瞭望塔 F 当成观鸟屋。"),
            "14": _q("D", "map", "野餐草坪在主楼西侧，对应 D。西北角的 Play area 已标出，不是本题。"),
            "15": _q("E", "map", "船库在东岸，靠近泻湖，对应 E。"),
            "16": _q("F", "map", "瞭望塔在北面沙嘴上，对应 F。与观鸟屋 C 是两处不同地点。"),
            "17": _q(
                "B",
                "matching",
                "Guided beach walks 只在周末进行。不是会员专属，也不需要提前预约。",
            ),
            "18": _q(
                "A",
                "matching",
                "Kayak hire 必须提前预订，因为名额有限。不要选周末才有或会员专属。",
            ),
            "19": _q(
                "C",
                "matching",
                "望远镜可凭入场票免费借用。先提到押金是干扰，随后说明凭票即可。",
            ),
            "20": _q(
                "D",
                "matching",
                "Evening talks 只在七月和八月举办。今年没有取消。",
            ),
            "21": _q(
                "B",
                "mcq",
                "Tomás 提到电脑出过问题，Jade 说只做了两周，但导师指出真正的问题是数据只覆盖午餐、没有晚餐。故选 B。",
            ),
            "22": _q(
                "A",
                "mcq",
                "Tomás 先建议称未上桌的食物，讨论后他们决定称盘子里剩下的食物。故选 A。",
            ),
            "23": _q(
                "C",
                "mcq",
                "导师反对在排队时采访，也反对把问卷做得太长，要求采访不超过十分钟。故选 C。",
            ),
            "24": _q(
                "B",
                "mcq",
                "问卷由 Aisha 来写；Jade 主动承担海报设计。联系厨房经理尚未有人接下。故选 B。",
            ),
            "25": _q(
                "C",
                "mcq",
                "系研讨会名额已满；他们改在校园可持续发展集市上展示。不是投稿学生期刊。故选 C。",
            ),
            "26": _q(
                "A",
                "mcq",
                "秤已经可以借用，学生参与也不太令他们担心；最大的顾虑是厨房员工是否合作。故选 A。",
            ),
            "27": _q("B", "matching", "文献综述由 Tomás 来写。他先推给 Aisha，后接受了。"),
            "28": _q("C", "matching", "伦理表格由 Aisha 完成，因为她做过类似表格。"),
            "29": _q("A", "matching", "预研究（pilot study）由 Jade 来做。"),
            "30": _q(
                "B",
                "matching",
                "Aisha 先说她去订会议室，后因要交伦理表改由 Tomás 预订。不要选 C。",
            ),
            "31": _q(
                "drains",
                "notes",
                "泥炭地变干是因为十九世纪修建了 drains。后面出现的 ditches 是早期田间沟，不是本题所要的词。",
                alternatives=["drain"],
                word_limit=WL2,
            ),
            "32": _q(
                "carbon",
                "notes",
                "干泥炭会向空气中释放 carbon。同句提到 heat 和 dust，但笔记对应 releases ... into the air 的是 carbon。",
                word_limit=WL2,
            ),
            "33": _q(
                "roads",
                "notes",
                "讲者先说 buildings，随即更正为 roads，并补充 bridges。笔记是 local ______，标准答案为 roads。填 roads and bridges 超过两个词，判错。",
                alternatives=["road"],
                word_limit=WL2,
            ),
            "34": _q(
                "2009",
                "notes",
                "有人以为是 2011 年，但讲者说明水泵实际在 2009 年关闭。不要填 2011 或 2012。",
                word_limit=WL2,
            ),
            "35": _q(
                "sluice gates",
                "notes",
                "水位现由 sluice gates 控制。pumps 已经关掉，不是现行控制方式。",
                alternatives=["sluice gate"],
                word_limit=WL2,
            ),
            "36": _q(
                "lapwings",
                "notes",
                "工程暂停是因为 lapwings 正在筑巢。geese 很多但不是停工原因。",
                alternatives=["lapwing"],
                word_limit=WL2,
            ),
            "37": _q(
                "hay",
                "notes",
                "农民得到的补偿是湿草甸上的 hay，可以出售；不是现金补贴。",
                word_limit=WL2,
            ),
            "38": _q(
                "eels",
                "notes",
                "出乎意料回归的是 eels。otters 是预期中的，不是 unexpected。",
                alternatives=["eel"],
                word_limit=WL2,
            ),
            "39": _q(
                "methane",
                "notes",
                "当前研究在测量 methane 排放。carbon 已在前面作为干泥炭的问题出现，不是正在测量的对象。",
                word_limit=WL2,
            ),
            "40": _q(
                "boardwalk",
                "notes",
                "访客中心的资金被取消，改为修建一条 boardwalk。不要填 visitor centre。",
                alternatives=["board walk", "board-walk"],
                word_limit=WL2,
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
    # Transcripts are filled from listening_script.py so both stay in sync.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from listening_script import transcripts_for_keys

    data = keys()
    data["transcripts"] = transcripts_for_keys()
    PAPER_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAPER_PATH.write_text(json.dumps(paper(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    KEYS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {PAPER_PATH}")
    print(f"Wrote {KEYS_PATH}")


if __name__ == "__main__":
    main()
