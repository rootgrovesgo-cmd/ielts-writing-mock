"""Original classroom totem used as a growth progress bar.

Eight stacked chibi creatures are drawn on a chunky pixel grid, not
copied from any official artwork or sprite sheet. Lighting fills inclusive
half-bands from the bottom (5.5) up to the student's best usable score, with
9.0 as the capstone at the top. Unlit figures are a single grey silhouette.
Official marks and logos are not used.

Usable scores are reading official/reference bands, listening official/reference
bands, and writing teacher bands only. Hidden writing official scores and
speaking scores are ignored.
"""

from __future__ import annotations

import html
from pathlib import Path

# Bottom-up order. A best band of 7.0 lights the first four stages.
STAGES: tuple[float, ...] = (5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0)
STAGE_IDS: tuple[str, ...] = (
    "duck",
    "turtle",
    "egg",
    "sprout",
    "pink",
    "lizard",
    "fox",
    "mouse",
)

TITLE = "成长进度"
EMPTY_STATUS = "暂无评分"
WAITING_STATUS = "待成长"

# Shared pixel palette. Letters in a sprite: see PALETTE. '.' is empty and is
# not part of the silhouette.
PALETTE: dict[str, str] = {
    "K": "#2a2826",  # charcoal eyes / mouth / feet
    "W": "#fffdf7",  # eye highlight
    "Y": "#f6d34a",  # yellow (mouse, duck, egg tufts)
    "H": "#ffea7a",  # yellow highlight
    "D": "#e0b03a",  # gold shadow / tail
    "B": "#7a4c22",  # brown ear tips
    "R": "#e05650",  # cheeks, tongue, triangles, mark
    "F": "#d2a06a",  # fox fur
    "T": "#9a6438",  # dark brown ears / feet
    "C": "#fff3d8",  # cream ruff / eggshell / bill
    "E": "#fffaf0",  # cream highlight
    "O": "#f09a64",  # orange lizard
    "N": "#e07848",  # deep orange mouth / feet / tail
    "A": "#f8d4b4",  # peach belly
    "P": "#f5b6c0",  # pink body
    "J": "#fbd0d6",  # pink highlight
    "I": "#e8909c",  # rose blush / inner ear / feet
    "L": "#7ec85e",  # leaf
    "V": "#4e9a4a",  # deep leaf
    "M": "#8ad8c4",  # mint sprout
    "G": "#b4ead8",  # mint highlight
    "S": "#5eae9c",  # teal spots / feet
    "Q": "#84d0ee",  # sky-blue turtle
    "U": "#5aa8d0",  # ocean shadow / blue triangle
    "X": "#d8c08c",  # tan shell / bill line
    "Z": "#c4a66c",  # khaki outline / shell edge / zigzag
}

COLOR_LETTERS = frozenset(PALETTE)

# 64-column sitting poses, indexed by stage id. Drawn on a denser grid
# than the earlier 32-column draft so facial features and signature marks
# stay sharp at the same on-screen width.
SPRITES: dict[str, tuple[str, ...]] = {
    # 9.0 capstone: yellow mouse, brown-tipped long ears, red cheeks, pointed tail.
    "mouse": (
        "................BB............................BB................",
        "...............BBBB..........................BBBB...............",
        "...............BYYB..........................BYYB...............",
        "...............BYYB..........................BYYB...............",
        "...............YYYY..........................YYYY...............",
        "...............YYYY..........................YYYY...............",
        "................YYYY........................YYYY................",
        "................YYYY........................YYYY................",
        ".................YYYY......................YYYY.................",
        ".................YYYY......................YYYY.................",
        "..................YYYY....................YYYY..................",
        "..................YYYY....................YYYY..................",
        "...................YYYY.......YYYY.......YYYY...................",
        "...................YYYY...YYYYYYYYYYYY...YYYY...................",
        "....................YYYYYYYYYYYYYYYYYYYYYYYY....................",
        "......................YYYYYYYYYYYYYYYYYYYY......................",
        "....................YYYYYYYYYYYYYYYYYYYYYYYY....................",
        "...................YYYYYYYYYYYYYYYYYYYYYYYYYY...................",
        "..................YYYYYHHHYYYYYYYYYYYYYYYYYYYY..................",
        "..................YYYYHHHHHYYYYYYYYYYYYYYYYYYY..................",
        ".................YYYYHHHHHHHYYYYYYYYYYYYYYYYYYY.................",
        ".................YYYYYHHHHHYYYYYYYYYYYYYYYYYYYY.................",
        "................YYYYYYYKKHYYYYYYYYYYYYYKKYYYYYYY................",
        "................YYYYYYKWKKYYYYYYYYYYYYKWKKYYYYYY................",
        "................YYYYYYYKKYYYYYYYYYYYYYYKKYYYYYYY................",
        "................YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY................",
        "................YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY................",
        "................YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY................",
        "................YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY................",
        "................YRRYYYYYYYYYYYYYYYYYYYYYYYYYRRYY................",
        "................RRRRYYYYYYYYYYYYYYYYYYYYYYYRRRR.................",
        ".................RRYYYYYYYYYYYYYYYYYYYYYYYYYRRY.................",
        "..................YYYYYYYYYYYYYYYYYYYYYYYYYYYY..................",
        "..................YYYYYYYYYYYKYYYYYKYYYYYYYYYY..................",
        "...................YYYYYYYYYYYKKKKKYYYYYYYYYY...................",
        "..................YYYYYYYYYYYYYYYYYYYYYYYYYYYY..................",
        "..............YY.YYYYYYYYYYYYYYYYYYYYYYYYYYYYYY.YY..............",
        "............YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY............",
        "...........YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY...........",
        "...........YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY...........",
        "...........YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY...........",
        "...........YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY...........",
        "............YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYD...........",
        "..............YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY.DDD..........",
        "................YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY....DDD.........",
        ".................YYYYYYYYYYYYYYYYYYYYYYYYYYYYYY....DDDB.........",
        "..................YYYYYYYYYYYYYYYYYYYYYYYYYYYY......DBBB........",
        "...................YYYYYYYYYYYYYYYYYYYYYYYYYY........BB.........",
        "....................YYYYYYYYYYYYYYYYYYYYYYYY..........B.........",
        "......................YYYYYYYYYYYYYYYYYYYY......................",
        "........................YYYYYYYYYYYYYYYY........................",
        "....................KKKKKKK.YYYYYYYY.KKKKKKK....................",
        "....................KKKKKKK..........KKKKKKK....................",
        ".....................KKKKK............KKKKK.....................",
        "................................................................",
        "................................................................",
    ),
    # 8.5: brown fox-like sitter, darker ear tips, fluffy cream ruff, blush.
    "fox": (
        "................................................................",
        "...........T........................................T...........",
        "..........TTT......................................TTT..........",
        "..........TFT......................................TFT..........",
        "..........TFFFT..................................TFFFT..........",
        "..........TFCCFT................................TFCCFT..........",
        "..........TFFCCFT..............................TFCCFFT..........",
        "...........FFCCCFT............................TFCCCFF...........",
        "............FFCCCFF........FFFFFFFFFF........FFCCCFF............",
        ".............FFFFFF.....FFFFFFFFFFFFFFFF.....FFFFFF.............",
        "..............FFFFFF...FFFFFFFFFFFFFFFFFF...FFFFFF..............",
        "...............FFFFF.FFFFFFFFFFFFFFFFFFFFFF.FFFFF...............",
        "....................FFFFFFFFFFFFFFFFFFFFFFFF....................",
        "...................FFFFFFFFFFFFFFFFFFFFFFFFFF...................",
        "..................FFFFFFFFFFFFFFFFFFFFFFFFFFFF..................",
        ".................FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF.................",
        ".................FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF.................",
        "................FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF................",
        "................FFFFFFFKKFFFFFFFFFFFFFFKKFFFFFFF................",
        "................FFFFFFKWKKFFFFFFFFFFFFKWKKFFFFFF................",
        "................FFFFFFFKKFFFFFFFFFFFFFFKKFFFFFFF................",
        "...............FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF...............",
        "...............FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF...............",
        "...............FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF...............",
        "................FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF................",
        "................FIIFFFFFFFFFFFFFFFFFFFFFFFFFIIFF................",
        "................IIIIFFFFFFFFFFFKKFFFFFFFFFFIIIIF................",
        "................FIIFFFFFFFFFFFFFFFFFFFFFFFFFIIFF................",
        ".................FFFFFFFFFFFFFFFFFFFFFFFFFFFFFF.................",
        ".................FFFFFFFFFFFFKFFFFFKFFFFFFFFFFF.................",
        "..................FFFFFFFFFFFFKKKKKFFFFFFFFFFF..................",
        "...................FFFFCCCCCCCCCCCCCCCCCCFFFF...................",
        "....................CCCCCCCCCCCCCCCCCCCCCCCC....................",
        ".................CCCCCCCCCCCCEEEEEECCCCCCCCCCCC.................",
        "................CCCCCCCCEEEEEEEEEEEEEEEECCCCCCCC................",
        "...............CCCCCCCEEEEEEEEEEEEEEEEEEEECCCCCCC...............",
        "..............CCCCCCCEEEEEEEEEEEEEEEEEEEEEECCCCCCC..............",
        "..............CCCCCCCEEEEEEEEEEEEEEEEEEEEEECCCCCCC..............",
        ".............CCCCCCCCCEEEEEEEEEEEEEEEEEEEECCCCCCCCC.............",
        "............CCCCCCCCCCCCCEEEEEECCEEEEEECCCCCCCCCCCCC............",
        "............CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC............",
        "...........CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC...........",
        "...........CCCCCCCCFFFFFFCCCCCCCCCCCCCCFFFFFFCCCCCCCC...........",
        "............CCCCCCFFFFFFFFCCCCCCCCCCCCFFFFFFFFCCCCCC............",
        ".............CCCCFFFFFFFFFFCCCCCCCCCCFFFFFFFFFFCCCC.............",
        "................FFFFFFFFFFFFCCCCCCCCFFFFFFFFFFFF................",
        "................FFFFFFFFFFFF...CC...FFFFFFFFFFFF................",
        "................FFFFFFFFFFFF........FFFFFFFFFFFF................",
        "................FFFFFFFFFFFF........FFFFFFFFFFFF................",
        ".................FFFFFFFFFF..........FFFFFFFFFF.................",
        "..................FFFFFFFF............FFFFFFFF..................",
        "..................TTTTTTT..............TTTTTTT..................",
        "..................TTTTTTT..............TTTTTTT..................",
        "...................TTTTT................TTTTT...................",
        "................................................................",
        "................................................................",
    ),
    # 8.0: orange lizard with a happy open mouth and a peach belly.
    "lizard": (
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "...........................OOOOOOOOOO...........................",
        "........................OOOOOOOOOOOOOOOO........................",
        "......................OOOOOOOOOOOOOOOOOOOO......................",
        ".....................OOOOOOOOOOOOOOOOOOOOOO.....................",
        "....................OOOOOOOOOOOOOOOOOOOOOOOO....................",
        "...................OOOOOOOOOOOOOOOOOOOOOOOOOO...................",
        "..................OOOOOOOOOOOOOOOOOOOOOOOOOOOO..................",
        ".................OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO.................",
        ".................OOOOKKOOOOOOOOOOOOOOOOOOKKOOOO.................",
        "................OOOOKWKKOOOOOOOOOOOOOOOOKWKKOOOO................",
        "................OOOOOKKOOOOOOOOOOOOOOOOOOKKOOOOO................",
        "................OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO................",
        "...............OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO...............",
        "...............OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO...............",
        "...............OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO...............",
        "...............OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO...............",
        "................OIIOOOOOOOOOOOOOOOOOOOOOOOOOIIOO................",
        "................IIIIOOOOOOOOOOOOOOOOOOOOOOOIIIIO................",
        "................OIIOOOOOOOOOOOOOOOOOOOOOOOOOIIOO................",
        ".................OOOOOOOOOOOOKKKKOOOOOOOOOOOOOO.................",
        ".................OOOOOOOOOOOKKKKKKOOOOOOOOOOOOO.................",
        "..................OOOOOOOOOKKKRRKKKOOOOOOOOOOO..................",
        "...................OOOOOOOOKKRRRRKKOOOOOOOOOO...................",
        "....................OOOOOOOOKKRRKKOOOOOOOOOO....................",
        "....................OOOOOOOOOKKKKOOOOOOOOOOO....................",
        "...................OOOOOOOOOOOOOOOOOOOOOOOOOO...................",
        "..................OOOOOOOOOOOOOOOOOOOOOOOOOOOO..................",
        ".................OOOOOOOOOOOAAAAAAAAOOOOOOOOOOO.................",
        "............OOOOOOOOOOOOOOAAAAAAAAAAAAOOOOOOOOOOOOOO............",
        "...........OOOOOOOOOOOOOOAAAAAAAAAAAAAAOOOOOOOOOOOOOO...........",
        "...........OOOOOOOOOOOOOAAAAAAAAAAAAAAAAOOOOOOOOOOOOO...........",
        "..........OOOOOOOOOOOOOAAAAAAAAAAAAAAAAAAOOOOOOOOOOOOO..........",
        "...........OOOOOOOOOOOOAAAAAAAAAAAAAAAAAAOOOOOOOOOOOO...........",
        "...........OOOOOOOOOOOAAAAAAAAAAAAAAAAAAAAOOOOOOOOOOO...........",
        "............OOOOOOOOOOAAAAAAAAAAAAAAAAAAAAOOOOOOOOOO............",
        "................OOOOOOOAAAAAAAAAAAAAAAAAAOOOOOOONNNN............",
        "................OOOOOOOAAAAAAAAAAAAAAAAAAOOOOOOO.NNNNN..........",
        ".................OOOOOOOAAAAAAAAAAAAAAAAOOOOOOO...NNNNN.........",
        "..................OOOOOOOAAAAAAAAAAAAAAOOOOOOO.....NNNNN........",
        "...................OOOOOOOOAAAAAAAAAAOOOOOOOO.......NNN.........",
        "....................OOOOOOOOOOAAAAOOOOOOOOOO.........N..........",
        "......................OOOOOOOOOOOOOOOOOOOO......................",
        "........................OOOOOOOOOOOOOOOO........................",
        "............................OOOOOOOO............................",
        "....................NNNNNNN..........NNNNNNN....................",
        "....................NNNNNNN..........NNNNNNN....................",
        ".....................NNNNN............NNNNN.....................",
        "................................................................",
        "................................................................",
    ),
    # 7.5: pink round creature, tiny pointed ears, a little green leaf in its mouth.
    "pink": (
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "........................P..............P........................",
        ".......................PPP............PPP.......................",
        "......................PPIPP..........PPIPP......................",
        "......................PPPPP.PPPPPPPP.PPPPP......................",
        ".......................PPPPPPPPPPPPPPPPPP.......................",
        ".......................PPPPPPPPPPPPPPPPPP.......................",
        "......................PPPPPPPPPPPPPPPPPPPP......................",
        "....................PPPPPPPPPPPPPPPPPPPPPPPP....................",
        "...................PPPPPPPPPPPPPPPPPPPPPPPPPP...................",
        "...................PPPPPPPPPPPPPPPPPPPPPPPPPP...................",
        "..................PPPPPPPPPPPPPPPPPPPPPPPPPPPP..................",
        ".................PPPPPPPPPPPPPPPPPPPPPPPPPPPPPP.................",
        "................PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP................",
        "................PPPPPPJJJJPPPPPPPPPPPPPPPPPPPPPP................",
        "...............PPPPPPJJJJJJPPPPPPPPPPPPPPPPPPPPPP...............",
        "...............PPPPPPPJJJJPPPPPPPPPPPPPPPPPPPPPPP...............",
        "...............PPPPPPPPKKPPPPPPPPPPPPPPKKPPPPPPPP...............",
        "..............PPPPPPPPKWKKPPPPPPPPPPPPKWKKPPPPPPPP..............",
        "..............PPPPPPPPPKKPPPPPPPPPPPPPPKKPPPPPPPPP..............",
        "..............PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP..............",
        "..............PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP..............",
        "..............PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP..............",
        ".............PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP.............",
        ".............PPPPIIPPPPPPPPPPPPPPPPPPPPPPPPPIIPPPPP.............",
        ".............PPPIIIIPPPPPPPPPPPPPPPPPPPPPPPIIIIPPPP.............",
        ".............PPPPIIPPPPPPPPPPPPPPPPPPPPPPPPPIIPPPPP.............",
        "..............PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP..............",
        "..............PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP..............",
        "..............PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP..............",
        "..............PPPPPPPPPPPPPPPPKKPPPPPPPPPPPPPPPPPP..............",
        "..............PPPPPPPPPPPPPPPPPLLLLVPPPPPPPPPPPPPP..............",
        "...............PPPPPPPPPPPPPPPPPLLLLVPPPPPPPPPPPP...............",
        "...............PPPPPPPPPPPPPPPPPPLLVVPPPPPPPPPPPP...............",
        "...............PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP...............",
        "................PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP................",
        "................PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP................",
        ".................PPPPPPPPPPPPPPPPPPPPPPPPPPPPPP.................",
        "..................PPPPPPPPPPPPPPPPPPPPPPPPPPPP..................",
        "...................PPPPPPPPPPPPPPPPPPPPPPPPPP...................",
        "...................PPPPPPPPPPPPPPPPPPPPPPPPPP...................",
        "....................PPPPPPPPPPPPPPPPPPPPPPPP....................",
        "......................PPPPPPPPPPPPPPPPPPPP......................",
        ".......................PPPPPPPPPPPPPPPPPP.......................",
        ".........................PPPPPPPPPPPPPP.........................",
        "............................PPPPPPPP............................",
        "................................................................",
        "................................................................",
        "....................IIIIIII..........IIIIIII....................",
        "....................IIIIIII..........IIIIIII....................",
        ".....................IIIII............IIIII.....................",
        "................................................................",
        "................................................................",
    ),
    # 7.0: mint plant-sprout with darker spots and a leaf-bulb on its back.
    "sprout": (
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        ".................MM................MM...........................",
        "................MSSMM.............MMSSM.........................",
        "................MMMMM....MMMMMMM..MMMMM.........................",
        ".................MMM..MMMMMMMMMMMMMMMM..........................",
        "....................MMMMMMMMMMMMMMMMM...........................",
        "...................MMMMMMMMMMMMMMMMMMM..........................",
        ".................MMMMMMMMMMMMMMMMMMMMMMM.....L..................",
        ".................MMMMMMMMMMMMMMMMMMMMMMM....LLL.................",
        "................MMMMMMMMMMMMMMMMMMMMMMMMM..LLVLL................",
        "...............MMMMMMMMGMMMMMMMMMMMMMMMMMMLLLLLLLL..............",
        "...............MMMMMMGGGGGMMMMMMMMMMMMMMMLLLLLLLLLL.............",
        "..............MMMMMMMGGGGGMMMMMMMMMMMMMMLLLLLLLLLLLL............",
        "..............MMMMMMMKKGGGMMMMMMMKKMMMMLLLLLLLLLLLLLL...........",
        "..............MMMMMMKWKKMMMMMMMMKWKKMMLLLLLLLLLLLLLLLL..........",
        ".............MMMMMMMMKKMMMMMMMMMMKKMMMLLLLLLLLLLLLLLLL..........",
        ".............MMMMMMMMMMMMMMMMMMMMMMMMLLLLLLLLLLLLLLLLLL.........",
        ".............MMMMMMMMMMMMMMMMMMMMMMMMLLLLLLLLLLLLLLLLLL.........",
        ".............MMMMMMMMMMMMMMMMMMMMMMMMLLLLLLLLLVVVLLLLLL.........",
        "..............MMMMMMMMMMMMMMMMMMMMMMMLLLLLLLLVVVVVLLLLL.........",
        "..............MMMMMMMMMMMMMMMMMMMMMMMLLLLLLLVVVVVVVLLLL.........",
        "..............MIIMMMMMMMMMMMMMMMMMMMMIILLLLLVVVVVVVLLLL.........",
        "..............IIIIMMMMMMMMMMMMMMMMMMIIIILLLLVVVVVVVLLLL.........",
        "...............IIMMMMMMMMMMMMMMMMMMMMIILLLLLVVLVVVVLLLL.........",
        "................MMMMMMMMMMMMMMMMMMMMMMLLLLLLLVVVVVLLLL..........",
        ".................MMMMMMMMKMMMMMKMMMMMMLLLLLLLLVVVLLLLL..........",
        ".................MMMMMMMMMKKKKKMMMMMMMMLLLLLLLLLLLLLL...........",
        "................MMMMMMMMMMMMMMMMMMMMMMMMLLLLLLLLLLLL............",
        "...............MMMMMMMMMMMMMMMMMMMMMMMMMMLLLLLLLLLL.............",
        "..............MMMMMMMMMMMMMMMMMMMMMMMMMMMMLLLLLLLL..............",
        "..........MMMMMMMMMMSSSSMMMMMMMMMMMMMMMMMMMMM...................",
        "..........MMMMMMMMMSSSSSSMMMMMMMMMMMMMMMMMMMMM..................",
        ".........MMMMMMMMMMSSSSSSMMMMMMMMMMMMMMMMMMMMMM.................",
        ".........MMMMMMMMMMSSSSSSMMMMMMMMMMMMMMMMMMMMMM.................",
        ".........MMMMMMMMMMMSSSSMMMMMMMSSSSMMMMMMMMMMMM.................",
        "..........MMMMMMMMMMMMMMMMMMMMSSSSSSMMMMMMMMMMM.................",
        "............MMMMMMMMMMMMMMMMMMSSSSSSMMMMMMMMM...................",
        ".............MMMMMMMMMMMSSSMMMSSSSSSMMMMMMMM....................",
        ".............MMMMMMMMMMSSSSSMMMMSSMMMMMMMMMM....................",
        "..............MMMMMMMMMSSSSSMMMMMMMMMMMMMMM.....................",
        "...............MMMMMMMMMSSSMMMMMMMMMMMMMMM......................",
        "................MMMMMMMMMMMMMMMMMMMMMMMMM.......................",
        ".................MMMMMMMMMMMMMMMMMMMMMMM........................",
        "...................MMMMMMMMMMMMMMMMMMM..........................",
        ".....................MMMMMMMMMMMMMMM............................",
        ".........................MMMMMMM................................",
        "..................SSSSSSS........SSSSSSS........................",
        "..................SSSSSSS........SSSSSSS........................",
        "...................SSSSS..........SSSSS.........................",
        "................................................................",
        "................................................................",
    ),
    # 6.5: cream eggshell baby, zigzag rim, red and blue triangles, yellow tufts.
    "egg": (
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "............................Y...................................",
        "........................Y..YYY..Y...............................",
        ".......................YYY.YDY.YYY..............................",
        ".......................YYY.YYY.YYY..............................",
        "........................Y..YYYCCYCCCC...........................",
        ".........................CCCYCCCCCCCCCC.........................",
        ".......................CCCCCCCCCCCCCCCCCC.......................",
        ".....................CCCCCCCCCCCCCCCCCCCCCC.....................",
        "....................CCCCCCCCCCCCCCCCCCCCCCCC....................",
        "...................CCCCCCCCCCCCCCCCCCCCCCCCCC...................",
        "...................CCCCCCCCCCCCCCCCCCCCCCCCCC...................",
        "..................CCCCCEEEECCCCCCCCCCCCCCCCCCC..................",
        ".................CCCCCEKKEEECCCCCCCCCCCKKCCCCCC.................",
        ".................CCCCCKWKKECCCCCCCCCCCKWKKCCCCC.................",
        ".................CCCCCCKKCCCCCCCCCCCCCCKKCCCCCC.................",
        "................CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC................",
        "................CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC................",
        "................CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC................",
        "................CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC................",
        "................CIICCCCCCCCCCCCCCCCCCCCCCCCCIICC................",
        "................IIIICCCCCCCCCCCCCCCCCCCCCCCIIIIC................",
        "................CIICCCCCCCCCCCCCCCCCCCCCCCCCIICC................",
        ".................CCCCCCCCCCCCCCCCCCCCCCCCCCCCCC.................",
        ".................CCCCCCCCCCCCKCCCCCKCCCCCCCCCCC.................",
        ".................CCCCCCCCCCCCCKKKKKCCCCCCCCCCCC.................",
        "..................CCCCCCCCCCCCCCCCCCCCCCCCCCCC..................",
        "..................CCCCCCCCCCCCCCCCCCCCCCCCCCCC..................",
        "...............Z.CCCZCCCCZCCCCZCCCCZCCCCZCCCCCC.................",
        "..............Z.ZCCZCZCCZCZCCZCZCCZCZCCZCZCCCCCC................",
        ".............Z.CCZZCCCZZCCCZZCCCZZCCCZZCCCZCCCCCC...............",
        ".............Z.ZZCCZZZCCZZZCCZZZCCZZZCCZZCZCCCCCC...............",
        ".............ZZZCCCCZCCCCZCCCCZCCCCZCCCCZZZCCCCCC...............",
        "...............CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC...............",
        "..............CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC..............",
        "..............CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC..............",
        "...............CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC...............",
        "...............CCCCCRCCCCCCCCCCCCCCCCCCCCCCUCCCCC...............",
        "...............CCCCRRRCCCCCCCCCCCCCCCCCCCCUUUCCCC...............",
        "...............CCCRRRRRCCCCCCCCCCCCCCCCCCUUUUUCCC...............",
        "................CRRRRRRRCCCCCCCCCCCCCCCCUUUUUUUC................",
        ".................CRRRRRCCCCCCCCCCCCCCCCCCUUUUUC.................",
        "..................CRRRCCCCCCCCCCCCCCCCCCCCUUUC..................",
        "...................CCCCCCCCCCCCCCCCCCCCCCCCCC...................",
        "....................CCCCCCCCCCCCCCCCCCCCCCCC....................",
        ".....................CCCCCCCCCCCCCCCCCCCCCC.....................",
        ".......................CCCCCCCCCCCCCCCCCC.......................",
        "..........................CCCCCCCCCCCC..........................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
    ),
    # 6.0: sky-blue turtle, sitting, tan shell tucked to one side, small smile.
    "turtle": (
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        ".......................QQQQQQQQQQ...............................",
        "....................QQQQQQQQQQQQQQQQ............................",
        "...................QQQQQQQQQQQQQQQQQQ...........................",
        "..................QQQQQQQQQQQQQQQQQQQQ..........................",
        "................QQQQQQQQQQQQQQQQQQQQQQQQ........................",
        "................QQQQQQQQQQQQQQQQQQQQQQQQ........................",
        "...............QQQQQQQQQQQQQQQQQQQQQQQQQQ.......................",
        "..............QQQQQQQQQQQQQQQQQQQQQQQQQQQQ......................",
        "..............QQQQQQQKKQQQQQQQQQQKKQQQQQQQ......................",
        ".............QQQQQQQKWKKQQQQQQQQKWKKQQQQQQQ.....................",
        ".............QQQQQQQQKKQQQQQQQQQQKKQQQQQQQQ.....................",
        ".............QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ.....................",
        ".............QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ.....................",
        ".............QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ.....................",
        ".............QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ.....................",
        ".............QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ.....................",
        ".............QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ.....................",
        ".............QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQXXXXX................",
        "..............QQQQQQQQQQQKQQQQQKQQQQQQQQQXXXXXXXXX..............",
        "..............QQQQQQQQQQQQKKKKKQQQQQQQQXXXXXXXXXXXXX............",
        "...............QQQQQQQQQQQQQQQQQQQQQQQXXXXXXXXXXXXXXX...........",
        "................QQQQQQQQQQQQQQQQQQQQQXXXXXXXXXXXXXXXXX..........",
        "................QQQQQQQQQQQQQQQQQQQQXXXXXCCCCCCXXXXXXXX.........",
        "................QQQQQQQQQQQQQQQQQQQQXXXXCCCCCCCCXXXXXXX.........",
        "...............QQQQQQQQQQQQQQQQQQQQXXXXCCCCCCCCCCXXXXXXX........",
        "..............QQQQQQQQQQQQQQQQQQQQQXXXXCCCCCCCCCCXXXXXXX........",
        "...........QQQQQQQQQQQQQQQQQQQQQQQXXXXXCCCCCCCCCCXXXXXXXX.......",
        "..........QQQQQQQQQQQQQQQQQQQQQQQQXXXXXCCCCCCCCCCXXXXXXXX.......",
        ".........QQQQQQQQQQQQQQQQQQQQQQQQQXXXXXCCCCCCCCCCXXXXXXXX.......",
        ".........QQQQQQQQQQQQQQQQQQQQQQQQQXXXXXXCCCCCCCCXXXXXXXXX.......",
        ".........QQQQQQQQQQQQQQQQQQQQQQQQQXXXXXXXCCCCCCZZZZXXXXXX.......",
        "..........QQQQQQQQQQQQQQQQQQQQQQQQXXXXXXXXXXXXZZZZZZXXXXX.......",
        "...........QQQQQQQQQQQQQQQQQQQQQQQXXXXXXXXXXXZZZZZZZZXXXX.......",
        ".............QQQQQQQQQQQQQQQQQQQQQQXXXXXXXXXXZZZZZZZZXXX........",
        ".............QQQQQQQQQQQQQQQQQQQQQQXXXXXXXXXXZZZZZZZZXXX........",
        "..............QQQQQQQQQQQQQQQQQQQQQQXXXXXXXXXZZZZZZZZXX.........",
        "..........UUUUUUQQQQQQQQQQQQQQQQQQQQXXXXXXXXXXZZZZZZXXX.........",
        ".........UUUUUUUUQQQQQQQQQQQQQQQQQQQQXXXXXXXXXXZZZZXXX..........",
        ".........UUUUUUUUQQQQQQQQQQQQQQQQQQQQQXXXXXXXXXXXXXXX...........",
        "..........UUUUUU..QQQQQQQQQQQQQQQQQQQQ.XXXXXXXXXXXXX............",
        "...................QQQQQQQQQQQQQQQQQQ....XXXXXXXXX..............",
        "......................QQQQQQQQQQQQ.........XXXXX................",
        "................................................................",
        "..................UUUUUUU.......UUUUUUU.........................",
        "..................UUUUUUU.......UUUUUUU.........................",
        "...................UUUUU.........UUUUU..........................",
        "................................................................",
        "................................................................",
    ),
    # 5.5: yellow duck, slightly dazed, rounded bill, a small red "!" beside the head.
    "duck": (
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................................................",
        "................................YYYYYYYY........................",
        ".....RR......................YYYYYYYYYYYYYY.....................",
        "....RRRR...................YYYYYYYYYYYYYYYYYY...................",
        "....RRRR..................YYYYYYYYYYYYYYYYYYYY..................",
        ".....RR.................YYYYYYYYYYYYYYYYYYYYYYYY................",
        ".....RR................YYHHHHYYYYYYYYYYYYYYYYYYYY...............",
        ".....RR................YHHHHHHYYYYYYYYYYYYYYYYYYY...............",
        ".....RR...............YYHHHHHHYYYYYYYYYYYYYYYYYYYY..............",
        ".....................YYYYHHHHYYYYYYYYYYYYYYYYYYYYYY.............",
        ".....RR..............YYYYYYYYYYYYYYYYYYYYYYKKYYYYYY.............",
        "....RRRR............YYYYYYYYYYYYYYYYYYYYYYKWKKYYYYYY............",
        ".....RR.............YYYYYYYYYYYYYYYYYYYYYYYKKYYYYYYY............",
        "....................YYYYYYYKKYYYYYYYYYYYYYYYYYYYYYYY............",
        "....................YYYYYYKWKKYYYYYYYYYYYYYYYYYYYYYY............",
        "....................YYYYYYYKKYYYYYYYYYYYYYYYYYYYYYYY............",
        "....................YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY............",
        "....................YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY............",
        "....................YYYYYYYYYYYYYYCCCCYYYYYYYYYYYYYY............",
        "....................YYYYYYYYYYCCCCCCCCCCCCYYYYYYYYYY............",
        ".....................YYYYYYYCCCCCCCCCCCCCCCCYYYYYYY.............",
        ".....................YYYYYYCCCCCEEEEEEEECCCCCYYYYYY.............",
        "......................YYYYCCCCCCEEEEEEEECCCCCCYYYY..............",
        ".......................YYYCCCCCCCCEEEECCCCCCCCYYY...............",
        ".......................YYYCCCCCCCCCCCCCCCCCCCCYYY...............",
        "........................YYCCCCCCCCCCCCCCCCCCCCYY................",
        "......................YYYYYCCCCCCXXXXXXXCCCCCYYYYY..............",
        ".....................YYYYYYYCCCCCCCCCCCCCCCCYYYYYYY.............",
        ".................YYYYYYYYYYYYYCCCCCCCCCCCCYYYYYYYYYYYYY.........",
        "...............YYYYYYYYYYYYYYYYYYYCCCCYYYYYYYYYYYYYYYYYYY.......",
        "..............YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY......",
        "..............YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY......",
        "..............YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY......",
        "..............YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY......",
        "...............YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY.......",
        ".................YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY.........",
        "...................YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY...........",
        "....................YYYYYYYYYYYYYYYYYYYYYYYYYYYYYYYY............",
        ".....................YYYYYYYYYYYYYYYYYYYYYYYYYYYYYY.............",
        "......................YYYYYYYYYYYYYYYYYYYYYYYYYYYY..............",
        ".......................YYYYYYYYYYYYYYYYYYYYYYYYYY...............",
        ".........................YYYYYYYYYYYYYYYYYYYYYY.................",
        "...........................YYYYYYYYYYYYYYYYYY...................",
        "..............................YYYYYYYYYYYY......................",
        ".........................KKKKKKK........KKKKKKK.................",
        ".........................KKKKKKK........KKKKKKK.................",
        "..........................KKKKK..........KKKKK..................",
        "................................................................",
        "................................................................",
    ),
}

_WRITING_TEACHER_KEYS = ("teacher_band", "teacher_score", "writing_teacher")
_READING_LISTENING_KEYS = (
    "band_estimate",
    "band",
    "reference_band",
    "official_band",
    "score",
)
_IGNORE_KEYS = frozenset({
    "official_score",
    "writing_official",
    "writing_official_score",
    "speaking",
    "speaking_band",
    "speaking_score",
})

_CSS_PATH = Path(__file__).resolve().parent / "static" / "growth_stack.css"


def stage_count() -> int:
    """Number of totem stages (always 8)."""
    return len(STAGES)


def stage_ids() -> tuple[str, ...]:
    """Stable bottom-up stage ids, matching STAGES."""
    return STAGE_IDS


def _parse_half_band(value) -> float | None:
    """Return an IELTS half-band in 0–9, or None if missing or invalid.

    Non-half-bands such as 7.2 are ignored, matching the fireworks rule.
    Booleans are rejected so True is not read as 1.0.
    """
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return None
    if number < 0 or number > 9:
        return None
    if abs(number * 2 - round(number * 2)) > 1e-9:
        return None
    return round(number * 2) / 2


def format_band(band) -> str | None:
    """Format a half-band with one decimal, e.g. '7.0'."""
    value = _parse_half_band(band)
    if value is None:
        return None
    return f"{value:.1f}"


def _first_band(data: dict, keys: tuple[str, ...]) -> float | None:
    for key in keys:
        if key in _IGNORE_KEYS:
            continue
        parsed = _parse_half_band(data.get(key))
        if parsed is not None:
            return parsed
    return None


def _bands_from(item) -> list[float]:
    """Collect usable module bands from a number, list, or dict."""
    found: list[float] = []
    if item is None or item == "":
        return found
    if isinstance(item, (list, tuple)):
        for part in item:
            found.extend(_bands_from(part))
        return found
    if not isinstance(item, dict):
        parsed = _parse_half_band(item)
        if parsed is not None:
            found.append(parsed)
        return found

    module = str(item.get("module") or item.get("kind") or "").strip().lower()
    if module == "speaking":
        return found
    if module == "writing":
        band = _first_band(item, _WRITING_TEACHER_KEYS)
        if band is not None:
            found.append(band)
        return found
    if module:
        band = _first_band(item, _READING_LISTENING_KEYS)
        if band is not None:
            found.append(band)
        return found

    for key in ("reading", "listening"):
        if key not in item:
            continue
        value = item[key]
        if isinstance(value, dict):
            found.extend(_bands_from({**value, "module": key}))
        else:
            parsed = _parse_half_band(value)
            if parsed is not None:
                found.append(parsed)

    if "writing" in item:
        value = item["writing"]
        if isinstance(value, dict):
            found.extend(_bands_from({**value, "module": "writing"}))
        else:
            parsed = _parse_half_band(value)
            if parsed is not None:
                found.append(parsed)

    for key in _WRITING_TEACHER_KEYS:
        if key == "writing" or key not in item:
            continue
        parsed = _parse_half_band(item.get(key))
        if parsed is not None:
            found.append(parsed)

    if not found:
        band = _first_band(item, _READING_LISTENING_KEYS)
        if band is not None:
            found.append(band)
    return found


def best_growth_band(scores=None) -> float | None:
    """Best usable band among reading, listening, and writing teacher scores.

    Accepts a single half-band, a list of half-bands or score dicts, or a
    dict of module bands. ``official_score`` and speaking values are never
    used. A bare ``writing`` number is treated as the teacher band. Returns
    None when nothing usable is present.
    """
    found = _bands_from(scores)
    return max(found) if found else None


def lit_stages(band) -> tuple[bool, ...]:
    """Inclusive bottom-up lighting flags for the eight stages.

    A band of 7.0 returns four True values then four False. Missing scores,
    non-half-bands, and values below 5.5 return eight False flags.
    """
    value = _parse_half_band(band)
    if value is None:
        return (False,) * len(STAGES)
    return tuple(stage <= value + 1e-9 for stage in STAGES)


def status_text(band) -> str:
    """Short status line for the widget header."""
    value = _parse_half_band(band)
    if value is None:
        return EMPTY_STATUS
    if value < STAGES[0]:
        return WAITING_STATUS
    return f"当前最高 {format_band(value)}"


def sprite_cells(sprite: tuple[str, ...] | list[str], *, lit: bool) -> dict:
    """Rasterise one ASCII sprite into template cells."""
    rows = tuple(sprite)
    if not rows:
        raise ValueError("Sprite must have at least one row")
    cols = len(rows[0])
    cells: list[dict] = []
    for row, line in enumerate(rows):
        if len(line) != cols:
            raise ValueError(f"Sprite row {row} is {len(line)} wide, expected {cols}")
        for color in line:
            if color == ".":
                cells.append({"empty": True, "lit": False, "color": ""})
                continue
            if color not in COLOR_LETTERS:
                raise ValueError(f"Unknown sprite color {color!r}")
            cells.append({"empty": False, "lit": bool(lit), "color": color})
    return {
        "cols": cols,
        "rows": len(rows),
        "cells": cells,
    }


def gallery(band=None, scores=None) -> dict:
    """Build the vertical totem for a records-page widget.

    If ``band`` is omitted, it is derived from ``scores`` via
    ``best_growth_band``. Stages in the returned list are top-down (9.0
    first) so they can be rendered as a stack.
    """
    if band is not None and band != "":
        resolved = _parse_half_band(band)
    else:
        resolved = best_growth_band(scores)
    flags = lit_stages(resolved)
    stages = []
    current_id = None
    for index in range(len(STAGES) - 1, -1, -1):
        stage_id = STAGE_IDS[index]
        is_lit = flags[index]
        if is_lit and current_id is None:
            current_id = stage_id
        raster = sprite_cells(SPRITES[stage_id], lit=is_lit)
        stages.append({
            "id": stage_id,
            "band": STAGES[index],
            "band_label": format_band(STAGES[index]),
            "lit": is_lit,
            "current": False,  # filled below once the capstone lit id is known
            **raster,
        })
    for item in stages:
        item["current"] = bool(item["lit"] and item["id"] == current_id)
    lit_n = sum(1 for item in stages if item["lit"])
    label = format_band(resolved)
    return {
        "title": TITLE,
        "band": resolved,
        "band_label": label,
        "status": status_text(resolved),
        "empty": lit_n == 0,
        "lit": lit_n,
        "total": len(STAGES),
        "stages": stages,
    }


def _widget_css() -> str:
    try:
        return _CSS_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def render(band=None, scores=None) -> str:
    """Return a self-contained HTML widget for the vertical growth stack."""
    data = gallery(band=band, scores=scores)
    css = _widget_css()
    empty_cls = " is-empty" if data["empty"] else ""
    band_attr = ""
    if data["band_label"]:
        band_attr = f' data-band="{html.escape(data["band_label"], quote=True)}"'
    aria = f'{data["title"]}，{data["status"]}'
    parts = [
        f'<aside class="growth-stack{empty_cls}"{band_attr} '
        f'aria-label="{html.escape(aria, quote=True)}">',
    ]
    if css.strip():
        parts.append(f"<style>\n{css}\n</style>")
    parts.append(f'<h2 class="growth-stack-title">{html.escape(data["title"])}</h2>')
    parts.append(f'<p class="growth-stack-status">{html.escape(data["status"])}</p>')
    parts.append('<ol class="growth-stack-totem">')
    for fig in data["stages"]:
        lit_cls = "is-lit" if fig["lit"] else "is-unlit"
        current_cls = " is-current" if fig["current"] else ""
        lit_words = "已点亮" if fig["lit"] else "未点亮"
        band_label = fig["band_label"] or ""
        parts.append(
            f'<li class="growth-stack-stage {lit_cls}{current_cls}" '
            f'data-stage="{html.escape(fig["id"], quote=True)}" '
            f'data-band="{html.escape(band_label, quote=True)}" '
            f'aria-label="{html.escape(f"{band_label} {lit_words}", quote=True)}">'
        )
        parts.append(
            f'<div class="growth-stack-sprite" style="--growth-cols: {fig["cols"]};" '
            f'role="img" aria-hidden="true">'
        )
        for cell in fig["cells"]:
            if cell["empty"]:
                parts.append('<span class="growth-stack-cell is-empty"></span>')
            elif cell["lit"]:
                color = html.escape(cell["color"], quote=True)
                parts.append(f'<span class="growth-stack-cell is-lit growth-{color}"></span>')
            else:
                parts.append('<span class="growth-stack-cell is-unlit"></span>')
        parts.append("</div>")
        parts.append(f'<span class="growth-stack-stage-band">{html.escape(band_label)}</span>')
        parts.append("</li>")
    parts.append("</ol>")
    parts.append("</aside>")
    return "\n".join(parts)


def _validate() -> None:
    if len(STAGES) != 8 or len(STAGE_IDS) != 8:
        raise RuntimeError("Growth stack must have exactly 8 stages")
    if STAGES != (5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0):
        raise RuntimeError("Growth stack stages must be 5.5 through 9.0")
    if set(SPRITES) != set(STAGE_IDS):
        raise RuntimeError("Growth stack sprites must match stage ids")
    seen: set[tuple[str, ...]] = set()
    for name in STAGE_IDS:
        rows = SPRITES[name]
        widths = {len(line) for line in rows}
        if len(widths) != 1:
            raise RuntimeError(f"Growth sprite {name!r} rows must all be the same width")
        if not rows or not rows[0]:
            raise RuntimeError(f"Growth sprite {name!r} is empty")
        letters = {ch for line in rows for ch in line if ch != "."}
        bad = letters - COLOR_LETTERS
        if bad:
            raise RuntimeError(f"Growth sprite {name!r} has invalid colors {bad}")
        if "K" not in letters:
            raise RuntimeError(f"Growth sprite {name!r} is missing outline color")
        key = tuple(rows)
        if key in seen:
            raise RuntimeError(f"Growth sprite {name!r} is a duplicate of another pose")
        seen.add(key)
        sprite_cells(rows, lit=True)
        sprite_cells(rows, lit=False)


_validate()
