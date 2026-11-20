#!/usr/bin/env python3
"""Original Listening Set D audio cues and readable transcripts.

Speech is written for practice only. It imitates Cambridge-style features
(paraphrase, distractors, a speaker changing their mind) but does not copy
any official or leaked paper.

TTS for this set uses a normal speaking rate (edge-tts rate +0%), not the
faster rate used on earlier sets.
"""

from __future__ import annotations

# Distinct neural voices (edge-tts). en-GB / en-AU only.
# Narrator matches Sets A–C. Other roles reuse the public catalog
# but with a different assignment from earlier sets.
VOICES = {
    "narrator": "en-GB-SoniaNeural",
    "tessa": "en-GB-LibbyNeural",
    "owen": "en-GB-RyanNeural",
    "duncan": "en-AU-WilliamMultilingualNeural",
    "imogen": "en-GB-MaisieNeural",
    "rohan": "en-GB-ThomasNeural",
    "holt": "en-AU-NatashaNeural",
    "durrant": "en-GB-RyanNeural",
}

SPEAKER_LABELS = {
    "narrator": "Narrator",
    "tessa": "Tessa",
    "owen": "Owen",
    "duncan": "Duncan Bell",
    "imogen": "Imogen",
    "rohan": "Rohan",
    "holt": "Dr Sabina Holt",
    "durrant": "Professor Alec Durrant",
}

LOOK = 25
CHECK = 30
TURN = 0.45
# Normal speaking speed for this set. Do not raise this to +25%.
TTS_RATE = "+0%"


def say(speaker: str, text: str) -> tuple:
    return ("say", speaker, text)


def pause(seconds: float = TURN) -> tuple:
    return ("pause", float(seconds))


def gap(seconds: float) -> tuple:
    return ("gap", float(seconds))


SECTION1 = [
    say("narrator", "This is the Academic Listening practice test, Set D."),
    pause(0.7),
    say(
        "narrator",
        "Section 1. You will hear a woman booking weekend workshops at a community orchard.",
    ),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 1 to 5."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 1 to 5."),
    pause(0.6),
    say(
        "tessa",
        "Hello, is that Willowfen Community Orchard? I'd like to book places on some of your weekend workshops.",
    ),
    pause(),
    say(
        "owen",
        "Yes, this is Owen in the office. Which workshops were you hoping to join?",
    ),
    pause(),
    say(
        "tessa",
        "Winter pruning, first of all. A neighbour told me it's on the twelfth of February.",
    ),
    pause(),
    say(
        "owen",
        "The twelfth is a staff training day, I'm afraid — the site is closed to the public then. The winter pruning workshop is on the nineteenth of February.",
    ),
    pause(),
    say("tessa", "The nineteenth, fine. And is it still twenty-five pounds? That's what the website says."),
    pause(),
    say(
        "owen",
        "That figure is from last year, and we haven't updated the page. The fee is thirty-two pounds now. We do charge thirty-five if a private group books the whole session, but the ordinary public fee is thirty-two.",
    ),
    pause(),
    say("tessa", "Thirty-two, got it. Should I bring anything? I was going to pack a pair of gloves."),
    pause(),
    say(
        "owen",
        "No need for gloves or waterproofs — we provide those. What you do need to bring is a pair of secateurs. We don't lend secateurs, so please bring your own.",
    ),
    pause(),
    say(
        "tessa",
        "Right. I'd also like the tree grafting workshop. I circled the eighteenth of March in my diary.",
    ),
    pause(),
    say(
        "owen",
        "The eighteenth is just an evening talk about fruit varieties, not a practical session. The grafting workshop itself is on the eighth of March.",
    ),
    pause(),
    say(
        "tessa",
        "The eighth. And I saw that one is forty-two pounds — I'll pay that. Do I need to bring a grafting knife? Or a camera? I'd like to photograph the technique.",
    ),
    pause(),
    say(
        "owen",
        "Knives and the rootstock are all provided, and we'd rather people didn't take photos during the demonstration. What we do ask you to bring is a notebook, so you can jot down the steps.",
    ),
    pause(0.6),
    say("narrator", "Before you hear the rest of the conversation, you have some time to look at questions 6 to 10."),
    gap(LOOK),
    say("narrator", "Now listen and answer questions 6 to 10."),
    pause(0.6),
    say(
        "tessa",
        "Then there's juice pressing. Is that the last Saturday of September? I thought I saw the thirtieth.",
    ),
    pause(),
    say(
        "owen",
        "We did have it down for the thirtieth of September, but the fruit won't be ready. We've moved the juice-pressing workshop to the fourth of October. Don't mix that up with the fourteenth of October — that's just an open day, and there's no pressing then.",
    ),
    pause(),
    say("tessa", "Fourth of October. The leaflet I picked up in town says thirty pounds."),
    pause(),
    say(
        "owen",
        "That's the family ticket, for two adults and two children. The individual fee is sixteen pounds fifty. There was an old web price of fifteen pounds as well, but that ended in the spring.",
    ),
    pause(),
    say("tessa", "Sixteen fifty. Shall I bring some of my own apples?"),
    pause(),
    say(
        "owen",
        "Please don't — we only press fruit from this orchard, for quality reasons. What you should bring is bottles, clean ones, to take the juice home. We haven't any spare bottles here.",
    ),
    pause(),
    say(
        "tessa",
        "Bottles, fine. And the last one, hedgerow planting — is that the twenty-seventh of October?",
    ),
    pause(),
    say(
        "owen",
        "It's the twenty-seventh, but of November, not October. The twenty-seventh of November. The fee is eighteen pounds, as advertised.",
    ),
    pause(),
    say("tessa", "November the twenty-seventh. Anything special to wear? I was going to come in trainers."),
    pause(),
    say(
        "owen",
        "Trainers really aren't suitable on the wet ground. You need to bring boots — sturdy ones. As I said, gloves are provided, so boots are the essential thing.",
    ),
    pause(),
    say(
        "tessa",
        "Boots. I'll book all four, under Tessa Kline. That's K-L-I-N-E.",
    ),
    pause(),
    say("owen", "Thank you, Tessa. I'll email a confirmation shortly."),
    pause(0.6),
    say("narrator", "That is the end of Section 1. You now have 30 seconds to check your answers."),
    gap(CHECK),
]


SECTION2 = [
    say(
        "narrator",
        "Section 2. You will hear a member of staff talking about a visit to a restored waterworks.",
    ),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 11 to 14."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 11 to 14."),
    pause(0.6),
    say(
        "duncan",
        "Good morning, and welcome to Holmestead Waterworks. My name is Duncan Bell, and I look after visitor services here. I'll start with a little practical advice, and then I'll talk about this weekend's engine demonstrations, before I take you around the plan of the site.",
    ),
    pause(0.5),
    say(
        "duncan",
        "A few of you have asked whether you should book a guided tour in advance. You don't need to do that. The guides wait in the Filter House, and you can simply join a group when you arrive.",
    ),
    pause(0.4),
    say(
        "duncan",
        "I would advise wearing shoes you don't mind getting damp, because the floors around the pumps can be wet, even in summer. That's the main thing I would ask you to think about before you go in.",
    ),
    pause(0.4),
    say(
        "duncan",
        "People also ask about bags. There used to be lockers by the café, but they're out of service this season, so please keep your bags with you rather than looking for somewhere to leave them.",
    ),
    pause(0.4),
    say(
        "duncan",
        "If you want to go up the tower, leave yourself plenty of time. The stair is slow, and the last entry is forty minutes before closing. It isn't a long climb, but it isn't something you can rush at the end of a visit.",
    ),
    pause(0.4),
    say(
        "duncan",
        "Some websites still say you should arrive before ten to miss the coach parties. That used to be true, but the coaches now arrive after lunch, so the mornings are actually the quietest time anyway. That old advice is out of date.",
    ),
    pause(0.6),
    say(
        "duncan",
        "Now, the engine demonstrations this weekend. They're held in the engine hall, so rain never stops them — we don't cancel because of the weather.",
    ),
    pause(0.4),
    say(
        "duncan",
        "Children are very welcome to watch, but they aren't allowed to help start either engine. I'm afraid that's a safety rule we have to keep to.",
    ),
    pause(0.4),
    say(
        "duncan",
        "Each demonstration begins with a short talk, about five minutes, on how the engine was used when the works were still pumping water for the city. Please try to be in the hall a little before the start so you don't miss that introduction.",
    ),
    pause(0.4),
    say(
        "duncan",
        "We've also reprinted an original operating manual, and you can buy a copy after the demonstration if you'd like to take one home.",
    ),
    pause(0.4),
    say(
        "duncan",
        "One last detail on the timetable. The little pump runs on the hour through the afternoon, but the large pumping engine is only started twice a day, at eleven and at two, so don't expect to see that one every hour.",
    ),
    pause(0.6),
    say("narrator", "Before you hear the rest of the talk, you have some time to look at questions 15 to 20."),
    gap(LOOK),
    say("narrator", "Now listen and answer questions 15 to 20."),
    pause(0.6),
    say(
        "duncan",
        "Now, please look at the plan of the site. We'll start at the main entrance, on Mill Lane, at the bottom of your plan. The car park fills the south-west corner, on your left as you come in, and the River Holm runs along the eastern edge, on the right of the plan.",
    ),
    pause(0.5),
    say(
        "duncan",
        "As soon as you come through the gate, you'll see a small brick office on your right, just inside the entrance and close to Mill Lane. That's the first-aid room. It isn't the older ticket booth further along by the river — that booth is locked, and it isn't staffed.",
    ),
    pause(0.5),
    say(
        "duncan",
        "If you turn left instead, don't try to chain a bicycle to the car-park fence. The bicycle racks are in the little recess between the entrance path and the car park, just inside the gate on that side.",
    ),
    pause(0.5),
    say(
        "duncan",
        "Walk up the central path towards the Filter House — that's the large building in the middle of the plan. Attached to its west wall, in the yard between the Filter House and the car park, there's a small office. That's the lost-property office. If you leave a coat or a camera, that's where it will be taken.",
    ),
    pause(0.5),
    say(
        "duncan",
        "Carry on past the west side of the Filter House, and in the north-west corner of the site, beyond the west path, you'll find a timber building. That's the education shed, where the school workshops are held. It isn't next to the cooling pond — it's in that far corner.",
    ),
    pause(0.5),
    say(
        "duncan",
        "A lot of visitors assume the picnic tables are on the lawn immediately north of the cooling pond, because that's the most open patch of grass. In fact, they're in the north-east corner, right beside the river. That's the only place we allow picnics.",
    ),
    pause(0.5),
    say(
        "duncan",
        "Finally, if you follow the river path down from those tables, you'll come to a small hut about halfway along the east side, between the Filter House and the river. That's the volunteer hut, where the weekend guides sign in. So that's the layout, and I hope you enjoy your visit.",
    ),
    pause(0.6),
    say("narrator", "That is the end of Section 2. You now have 30 seconds to check your answers."),
    gap(CHECK),
]


SECTION3 = [
    say(
        "narrator",
        "Section 3. You will hear two students discussing a greywater project with their tutor.",
    ),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 21 to 26."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 21 to 26."),
    pause(0.6),
    say(
        "holt",
        "Imogen, Rohan, thank you for coming in. I read the outline of your greywater trial at Hatherley Sports Centre. Before we talk about the stages of the work, can I ask what in the background reading was actually new to both of you?",
    ),
    pause(),
    say(
        "imogen",
        "Well, we'd already been told in lectures how much drinking water the showers use, so that wasn't a surprise. What I hadn't taken in — and Rohan hadn't either — was how quickly untreated greywater becomes unsafe. We both thought it stayed usable for days, but the papers say it can be unsafe within hours.",
    ),
    pause(),
    say(
        "rohan",
        "Yes, that caught both of us out. The other thing we both found unexpected was how little energy a small treatment unit requires. I'd assumed it would be a serious load on the building's electricity, but the figures were tiny.",
    ),
    pause(),
    say(
        "imogen",
        "There was an article that claimed a lot of sports centres already reuse shower water, but that figure was for hotels, not sports centres, so we didn't treat it as a finding we could use.",
    ),
    pause(),
    say(
        "rohan",
        "And the rules on water colour are strict, but that didn't surprise Imogen — her sister works in environmental health — so I wouldn't say it was a surprise for both of us.",
    ),
    pause(0.5),
    say(
        "holt",
        "Good. You also looked at a previous student project on the same site. Rohan, what impressed you about that one?",
    ),
    pause(),
    say(
        "rohan",
        "Two things, really. First, the way costs were set out. They didn't just give a total — they broke the figures down so you could see which parts of the system were expensive. I want us to do that.",
    ),
    pause(),
    say(
        "imogen",
        "I thought the photographs were excellent, actually.",
    ),
    pause(),
    say(
        "rohan",
        "They were fine, but they didn't really add much for me — I wouldn't single them out. What did impress me, though, was the decision to test two systems side by side. That made the comparison much more convincing than testing one system on its own.",
    ),
    pause(),
    say(
        "holt",
        "And the sample size? They interviewed quite a few staff, didn't they?",
    ),
    pause(),
    say(
        "rohan",
        "That's just it — the sample was actually quite small. I wouldn't hold that up as a strength. They did include some interviews with cleaning staff, but those were very brief, so that wasn't what impressed me either.",
    ),
    pause(0.5),
    say(
        "holt",
        "All right. Looking ahead, is there anything you both think should be added to the report?",
    ),
    pause(),
    say(
        "rohan",
        "I was keen to include a comparison with rainwater harvesting, but Imogen pointed out we haven't collected any data on that, so we've dropped it.",
    ),
    pause(),
    say(
        "imogen",
        "I would have liked to include the views of swimmers, and you suggested that too, Dr Holt, but Rohan is right that we won't have time to interview them properly, so we don't agree on putting that in.",
    ),
    pause(),
    say(
        "rohan",
        "What we do both want in the report is the risk of legionella. We can't ignore that if we're storing used shower water, even for a short time.",
    ),
    pause(),
    say(
        "imogen",
        "Yes, that's essential. And we also both want to include the payback period for the equipment. The manager will ask how long it takes to recover the cost, so that has to be in there.",
    ),
    pause(),
    say(
        "holt",
        "The manager also asked about a plan for weekend opening. Have you included that?",
    ),
    pause(),
    say(
        "imogen",
        "We talked about it, but we both decided it's outside the brief. We're looking at the water system, not the centre's opening hours.",
    ),
    pause(0.6),
    say("narrator", "Before you hear the rest of the discussion, you have some time to look at questions 27 to 30."),
    gap(LOOK),
    say("narrator", "Now listen and answer questions 27 to 30."),
    pause(0.6),
    say(
        "holt",
        "Let's go through the stages of the trial in order, so I can see how the work actually unfolded.",
    ),
    pause(),
    say(
        "imogen",
        "First we had to select which showers to include. We thought the manager might take days to decide, but in the end that stage was completed in a single afternoon. We'd also expected the cleaning team to object, but they were actually quite helpful, so there was no opposition from them.",
    ),
    pause(),
    say(
        "rohan",
        "Then we took the baseline meter readings, before any of the new pipework went in. I started with a paper notebook, but Imogen suggested we put everything in a shared spreadsheet so we could both check the figures, and that's how the readings were recorded.",
    ),
    pause(),
    say(
        "holt",
        "And installing the diversion valves — did that stay on the original timetable?",
    ),
    pause(),
    say(
        "imogen",
        "No. We hoped to do it in term time, but the plumber could only come in the break, so that stage was delayed until the vacation. There was a leak in a waste pipe while he was there, and for a moment we thought we'd have to abandon the trial, but it was a joint on an old sink, not our valves, so we carried on.",
    ),
    pause(),
    say(
        "rohan",
        "The valves themselves were paid for by a department grant, which we'd already secured in the spring, so that wasn't something that happened at the installation stage.",
    ),
    pause(),
    say(
        "holt",
        "And after you'd collected the results, you presented them to the estates committee.",
    ),
    pause(),
    say(
        "imogen",
        "Yes. The presentation went reasonably well, and it was followed by a short written briefing — they asked us to leave a one-page summary for members who couldn't attend. That briefing came after the presentation, not instead of it.",
    ),
    pause(),
    say(
        "holt",
        "That's a clear sequence. Write it up in that order, and we'll talk about the draft next week.",
    ),
    pause(0.6),
    say("narrator", "That is the end of Section 3. You now have 30 seconds to check your answers."),
    gap(CHECK),
]


SECTION4 = [
    say("narrator", "Section 4. You will hear a lecture on restoring a lowland raised bog."),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 31 to 40."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 31 to 40."),
    pause(0.6),
    say("durrant", "Good afternoon. Today we're considering the restoration of lowland raised bogs: wetlands where partially decayed vegetation has accumulated into a dome of peat. Unlike a river-fed marsh, the upper surface of an intact raised bog depends mainly on rainfall. My example is an invented field project at Merewick Moss, a former peat-cutting site. We'll use it to explore why simply making a place look wet can be a very poor test of ecological recovery."),
    pause(0.5),
    say("durrant", "First, think about what we're trying to preserve. Plants continue to grow on a bog, but their dead remains break down unusually slowly. You might put that down to low temperature, and temperature certainly matters. However, the key effect of keeping the peat saturated is that it restricts the entry of oxygen. Many of the organisms that would otherwise consume the dead material cannot work as effectively under those conditions. Drain the site, and you remove that constraint: a store built up over centuries can then start losing carbon, even if the remaining surface still looks green."),
    pause(0.5),
    say("durrant", 'At Merewick, the obvious legacy of peat cutting was a network of drainage channels. Closing their outlets seemed an adequate first step. Initially, the team blamed continuing water loss on badly fitted barriers; after all, water levels were falling behind several of them. Inspections showed that the barriers themselves were intact. During dry weather, the peat beside them had shrunk, opening cracks through which water escaped around the structures. Adding height to each barrier would therefore have missed the actual route of leakage. The surrounding damaged peat had to be dealt with as well.'),
    pause(0.5),
    say("durrant", 'This diagnosis also changed the layout of the work. A contractor had offered a price based on putting a barrier at regular intervals, which looked simple on the budget sheet. The ecologists insisted on surveying the slope along each channel before choosing the distances between barriers. Where the ground fell rapidly, the structures needed to be closer together, so that no single one held back too great a difference in water level. The length of a channel told them roughly how much work was involved; it did not, by itself, determine the spacing.'),
    pause(0.5),
    say("durrant", "Most channels could be blocked using compacted peat from the site. At two outlets on the eastern edge, however, too little suitable peat remained to make a reliable seal. Timber was considered for the main barrier, then rejected there. What was installed instead was plastic, supplied as sheets whose edges locked together and driven into firm material below the channel. Some wood was used as bracing, which explains why photographs can be misleading about the barrier's composition. This was a limited exception, not a recommendation to put that material across the whole bog; inspection and eventual replacement remained part of the plan."),
    pause(0.5),
    say("durrant", 'Another intervention concerned the vegetation that had moved in after drainage. Willow lined a neighbouring stream, but that was outside the raised-bog restoration area. On the dried peat itself, birch had become established, and its removal was intended chiefly to reduce the amount of water being drawn up and released through leaves. Shade was another influence, but not the main reason for this decision. Tree removal can sound like the opposite of conservation; here, retaining woodland would have maintained a condition created by drainage, rather than restored the naturally open bog.'),
    pause(0.5),
    say("durrant", 'Rewetting did not guarantee that peat-forming mosses would return unaided. Across the old cutting fields, suitable fragments were scarce, so the team arranged a carefully limited transfer from a donor area. The nearest apparently healthy patch would have been convenient, but convenience was not the deciding factor. Before collecting anything, they compared the acidity of water in the donor and receiving areas. A moss community from chemically different conditions might fail even where the destination was equally wet. That check came before the agreement on how much material could safely be taken, not after a failed planting trial.'),
    pause(0.5),
    say("durrant", 'Once spread, the moss fragments were especially vulnerable: there was no established carpet around them to maintain a humid surface. The team covered them with a loose layer of straw. Its immediate job was to soften the effects of drying air and sharp temperature changes, rather than to supply a meal for the plants. The argument for it was therefore different from an argument for fertiliser. Nor was a deep covering desirable: the fragments still needed light. In the trial, the thickness of the layer was checked as carefully as the amount of moss beneath it.'),
    pause(0.5),
    say("durrant", 'How, then, could the team judge progress? A photograph of standing water after a storm was easy to obtain but told them little about conditions between rainstorms. For the regular water-level measurements, they relied on shallow wells, sunk at fixed points across the site. Sensors were lowered inside these, rather than left in the nearest visible pool. Each measurement was related to the adjacent peat surface. That distinction mattered because water could remain in a channel while the peat a few metres away was already becoming too dry for the recovering mosses.'),
    pause(0.5),
    say("durrant", 'Climate benefits required a separate set of measurements. The team expected less carbon dioxide to be released as the peat became wetter. That expectation was reasonable, but it was not enough to demonstrate an immediate overall improvement in the greenhouse-gas balance. Methane can increase when oxygen-poor conditions return, particularly where restoration creates persistent open water. The team therefore measured that gas as well. A rise did not prove that rewetting had been a mistake, any more than a fall in carbon dioxide alone proved complete success: both needed to be assessed over time.'),
    pause(0.5),
    say("durrant", "Finally, the annual average water level could conceal quite different patterns. Two areas might have the same mean, although one stayed fairly stable and the other alternated between flooding and severe drying. To test resilience, the researchers recorded how long water levels took to recover after a drought. They weren't just asking whether the surface became wet again with the first rain, but whether near-surface levels were re-established and maintained. That response, compared across restored and less-disturbed plots, was more informative than another attractive winter photograph. Restoration is a recovery of processes, not simply a change in appearance."),
    pause(0.5),
    say("narrator", "That is the end of Section 4. You now have 30 seconds to check your answers."),
    gap(CHECK),
    say("narrator", "That is the end of the Listening test. You now have some time to check your answers."),
]


SECTIONS = {
    1: SECTION1,
    2: SECTION2,
    3: SECTION3,
    4: SECTION4,
}


def _format_transcript(cues: list) -> str:
    lines: list[str] = []
    for cue in cues:
        if cue[0] != "say":
            continue
        _, speaker, text = cue
        label = SPEAKER_LABELS.get(speaker, speaker)
        lines.append(f"{label}: {text}")
    return "\n\n".join(lines)


def transcripts_for_keys() -> dict[str, str]:
    return {str(sid): _format_transcript(cues) for sid, cues in SECTIONS.items()}


def word_counts() -> dict[int, int]:
    out = {}
    for sid, cues in SECTIONS.items():
        words = 0
        for cue in cues:
            if cue[0] == "say":
                words += len(cue[2].split())
        out[sid] = words
    return out


if __name__ == "__main__":
    for sid, n in word_counts().items():
        print(f"Section {sid}: {n} spoken words")
        sil = sum(c[1] for c in SECTIONS[sid] if c[0] in {"pause", "gap"})
        print(f"  silences {sil:.0f}s, speech ~{n/150*60:.0f}s, total ~{sil + n/150*60:.0f}s")
