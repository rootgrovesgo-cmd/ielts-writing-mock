#!/usr/bin/env python3
"""Original Listening Set B audio cues and readable transcripts.

Speech is written for practice only. It imitates Cambridge-style features
(paraphrase, distractors, a speaker changing their mind) but does not copy
any official or leaked paper.
"""

from __future__ import annotations

# Distinct neural voices (edge-tts). en-GB / en-AU only.
# Names and voices are different from Set A, except the shared narrator.
VOICES = {
    "narrator": "en-GB-SoniaNeural",
    "priya": "en-GB-MaisieNeural",
    "marcus": "en-GB-RyanNeural",
    "elise": "en-AU-NatashaNeural",
    "maya": "en-GB-LibbyNeural",
    "tom": "en-AU-WilliamMultilingualNeural",
    "calder": "en-GB-ThomasNeural",
    "cole": "en-GB-LibbyNeural",
}

SPEAKER_LABELS = {
    "narrator": "Narrator",
    "priya": "Priya",
    "marcus": "Marcus",
    "elise": "Elise Ward",
    "maya": "Maya",
    "tom": "Tom",
    "calder": "Dr Calder",
    "cole": "Professor Miriam Cole",
}

LOOK = 25
CHECK = 30
TURN = 0.45


def say(speaker: str, text: str) -> tuple:
    return ("say", speaker, text)


def pause(seconds: float = TURN) -> tuple:
    return ("pause", float(seconds))


def gap(seconds: float) -> tuple:
    return ("gap", float(seconds))


SECTION1 = [
    say("narrator", "This is the Academic Listening practice test, Set B."),
    pause(0.7),
    say(
        "narrator",
        "Section 1. You will hear a woman booking a weekend stained-glass workshop at a craft centre.",
    ),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 1 to 5."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 1 to 5."),
    pause(0.6),
    say(
        "priya",
        "Hello, is that Hartwell Craft Centre? I'd like to book a place on the weekend stained-glass workshop.",
    ),
    pause(),
    say(
        "marcus",
        "Yes, this is Marcus at the bookings desk. The next weekend workshop — people often assume it's the twelfth, because that's still on our homepage, but that date is for the midweek evening class. The weekend stained-glass workshop is on the nineteenth.",
    ),
    pause(),
    say("priya", "The nineteenth. Not the twenty-sixth? A friend thought it had been moved."),
    pause(),
    say(
        "marcus",
        "No, we did consider the twenty-sixth when the tutor had a conflict, but that's been resolved. So it's the nineteenth.",
    ),
    pause(),
    say("priya", "And which studio is it in? I saw a photo of the Oak Studio."),
    pause(),
    say(
        "marcus",
        "The Oak Studio is being refurbished this month, so we won't use that. The stained-glass weekend is in the Willow Studio — that's the long room with the north-facing windows. Not the courtyard studio either; that's for pottery.",
    ),
    pause(),
    say("priya", "The Willow Studio. How do you spell Willow?"),
    pause(),
    say("marcus", "W-I-L-L-O-W. Willow Studio."),
    pause(),
    say("priya", "Thanks. What do we need to bring? I was going to buy some glass this week."),
    pause(),
    say(
        "marcus",
        "No need. We provide the coloured glass and the lead came. You might have read that students bring their own tools, but that's only for the advanced evening course. For this weekend, the tools stay in the studio. Do bring old clothes, though, and a pair of closed shoes. But the materials themselves — the coloured glass and the lead — are provided.",
    ),
    pause(),
    say("priya", "Coloured glass. Is there anything else I can add on? I thought there was a mosaics class."),
    pause(),
    say(
        "marcus",
        "There is a mosaics workshop, but that's in May, and it's already full. On the Sunday afternoon, after the stained-glass session, we run an optional jewellery class — small pieces, using leftover glass. Pottery is also happening in another building that day, but that isn't linked to this booking.",
    ),
    pause(),
    say("priya", "Jewellery. I'll think about that. And the fee? I had written down ninety-five pounds."),
    pause(),
    say(
        "marcus",
        "That's the midweek two-day course, which is ninety-five. There's also a student standby rate of sixty, but that's only if a place frees up on the Friday. The weekend workshop itself is eighty-five pounds. We do take a forty-five pound deposit when you book, but the course fee is eighty-five.",
    ),
    pause(),
    say("priya", "Eighty-five. Got it."),
    pause(0.6),
    say(
        "narrator",
        "Before you hear the rest of the conversation, you have some time to look at questions 6 to 10.",
    ),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 6 to 10."),
    pause(0.6),
    say("priya", "What does that include? A friend said I'd have to arrange my own lunch."),
    pause(),
    say(
        "marcus",
        "Lunch is included, actually. Transport isn't, and we don't provide accommodation — most people are local. Tea and coffee are free throughout the day anyway, whether you book or not. What the fee specifically includes, besides lunch, is insurance. We had a few people ask about that, because you're working with glass.",
    ),
    pause(),
    say("priya", "Lunch and insurance. Good. Are there facilities on site? I thought you had a café."),
    pause(),
    say(
        "marcus",
        "The café is closed this weekend because of staff training, and the shop only opens on weekdays. What we do have on site is a small gallery, where finished work from previous courses is displayed. You're welcome to walk through it during the lunch break.",
    ),
    pause(),
    say("priya", "A gallery. And parking?"),
    pause(),
    say(
        "marcus",
        "Don't use the west car park — that's for staff only — and the spaces at the front are reserved for deliveries on Saturday mornings. Visitors should use the east car park. It's a little further from the entrance, but it's clearly signed.",
    ),
    pause(),
    say("priya", "East car park. How do I find the centre? My map app wanted to send me to Station Road."),
    pause(),
    say(
        "marcus",
        "That happens a lot, because the old postcode still points to Station Road. We're actually on Maple Lane, directly opposite the old bakery. There's a dark green sign on the wall. Maple is spelled M-A-P-L-E. Once you're opposite the bakery, you can't miss us.",
    ),
    pause(),
    say(
        "priya",
        "Maple Lane, opposite the bakery. Is there anywhere nearby if I need to buy something? I thought there was a bookshop.",
    ),
    pause(),
    say(
        "marcus",
        "The bookshop closed last year, unfortunately. There's a café on the corner, but it isn't open until ten, which is after we start. The most useful place nearby is a pharmacy, just a minute's walk towards the bridge, if you need anything.",
    ),
    pause(),
    say("priya", "A pharmacy. That's all I need. Please book me in for the nineteenth."),
    pause(),
    say("marcus", "Willow Studio, the nineteenth. I'll email a confirmation this afternoon."),
    pause(),
    say("priya", "Thank you."),
    pause(0.6),
    say("narrator", "That is the end of Section 1. You now have 30 seconds to check your answers."),
    gap(CHECK),
]


SECTION2 = [
    say(
        "narrator",
        "Section 2. You will hear a guide giving a welcome talk at the start of a visit to a historic mill.",
    ),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 11 to 15."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 11 to 15."),
    pause(0.6),
    say(
        "elise",
        "Good morning, everyone, and welcome to Rivermead Heritage Mill. My name is Elise Ward, and I'll be leading your visit this morning. I'm glad so many of you have come, some from quite a distance.",
    ),
    pause(0.5),
    say(
        "elise",
        "Before we set off, a word about tickets, because a few of the details have changed this season. Some of you asked whether weekend tickets are cheaper if you buy them online. They aren't — the price at the desk is the same as the website, including at weekends. What I do need to mention is the student rate: it is reduced, but only if you can show a valid student card. We can't apply the discount without it. An audio guide is available, but it is not included in the ticket; it's a small extra charge at the desk. And tickets are for a specific date, so if the mill feels busy you can't simply come back tomorrow on the same ticket. Children under five, however, do not need a ticket at all — they are admitted free, provided an adult is with them.",
    ),
    pause(0.5),
    say(
        "elise",
        "Now, the main tour route itself. It takes in three particular attractions I want to highlight, so you know what you will actually see. First, you will see a restored water wheel, which we'll stop beside in a moment. Second, the miller's cottage, furnished as it was in the eighteen eighties. And third, a working loom room, where cloth is still produced on two of the original machines. I should be clear about what is not on this route. The Victorian schoolroom is in a separate building and needs a different ticket, so we won't go there this morning. The underground ice house would have been fascinating, but it's closed for repairs until next spring. And although ticket-holders may use the riverside picnic lawn after the tour, it isn't one of the attractions we visit as a group.",
    ),
    pause(0.6),
    say(
        "narrator",
        "Before you hear the rest of the talk, you have some time to look at questions 16 to 20.",
    ),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 16 to 20."),
    pause(0.6),
    say(
        "elise",
        "Let me explain what you'll actually do at each stop, because the programme has changed a little since last year, and some of the printed leaflets are already out of date.",
    ),
    pause(0.4),
    say(
        "elise",
        "The first stop is the entrance hall. We used to begin by watching grain being weighed, but we don't do that any more — the old scales are too fragile. Instead, you'll look at old photographs, a set we've newly mounted, showing the mill through the last century. So that's the first stop: the photographs, not the weighing.",
    ),
    pause(0.4),
    say(
        "elise",
        "The second stop is the wheel house. There you'll try a short milling demonstration — you'll take a turn at the hopper under supervision. It isn't just a talk; you do get to try it yourselves.",
    ),
    pause(0.4),
    say(
        "elise",
        "The third stop is the bakehouse. I know some of you hoped to collect a souvenir booklet there, but booklets are only in the shop at the end, not as part of a stop. In the bakehouse, you'll taste traditionally baked bread, made with flour from this mill. That's the activity at the third stop: tasting the bread.",
    ),
    pause(0.4),
    say(
        "elise",
        "The fourth stop is the finishing room. School groups sometimes measure the river depth from the window there, but that's a separate activity tomorrow and not for today's visit. What you will do is help to dye a sample of cloth, using the plant dyes the mill still prepares. So, a short dyeing activity, not a measurement.",
    ),
    pause(0.4),
    say(
        "elise",
        "The last stop is the archive loft. It isn't a shop moment and it isn't another demonstration. You'll hear a recorded interview with the last miller, who retired in nineteen ninety-eight. We play a short extract, and there's time for questions afterwards.",
    ),
    pause(0.5),
    say(
        "elise",
        "So, to recap briefly: photographs at the first stop, then a milling demonstration, then bread in the bakehouse, then dyeing a sample, and finally the recorded interview. The shop will be open as you leave if you do want that booklet. If there are no questions, we'll start at the entrance hall in a moment.",
    ),
    pause(0.6),
    say("narrator", "That is the end of Section 2. You now have 30 seconds to check your answers."),
    gap(CHECK),
]


SECTION3 = [
    say(
        "narrator",
        "Section 3. You will hear two students, Maya and Tom, discussing a project with their tutor, Doctor Calder.",
    ),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 21 to 26."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 21 to 26."),
    pause(0.6),
    say(
        "calder",
        "So, Maya and Tom, you're looking at night-time noise in Elm Court, one of the campus residences. Let's start with the aim of the project, because I want that to be quite sharp.",
    ),
    pause(),
    say(
        "maya",
        "We did wonder about comparing Elm Court with the new block across the road, and we also looked at a new type of meter the physics department has, but we decided that wasn't really the point.",
    ),
    pause(),
    say(
        "tom",
        "Yes. What we really want to find out is how noise affects students' sleep — not just how loud the building is, but whether people actually sleep worse.",
    ),
    pause(),
    say("calder", "Good. That's a clear objective."),
    pause(),
    say(
        "calder",
        "Have you sorted the practicalities? Equipment, permissions, the deadline?",
    ),
    pause(),
    say(
        "tom",
        "The recording equipment is already booked, and we agreed the deadline with you last week, so those two are fine.",
    ),
    pause(),
    say(
        "maya",
        "Oh — I've just realised we forgot something. We were so focused on the meters that we never got written permission from the residents. We talked to a few people informally, but we don't have anything in writing.",
    ),
    pause(),
    say(
        "calder",
        "Yes, you need that before you place any equipment. Informal chats aren't enough.",
    ),
    pause(),
    say(
        "calder",
        "Looking at your plan, I have a suggestion. You've listed weeknights only, Sunday to Thursday. I'd leave the number of rooms as it is — ten is enough — and you don't have to interview the facilities manager first, though you can later if you want background. What I would change is to include weekend nights as well as weekdays, because the noise profile may be quite different.",
    ),
    pause(),
    say("maya", "That makes sense. We'll add Friday and Saturday."),
    pause(),
    say("calder", "And how do you want to collect the data?"),
    pause(),
    say(
        "tom",
        "I don't think standing in the corridors with a handheld meter will work — we'd disturb people, and we'd only get a snapshot. A diary on its own is too subjective, though we might use a short one as a supplement. I'd like to leave meters in the rooms overnight, so we get a full record without us being there.",
    ),
    pause(),
    say("calder", "That's the right method, provided the residents agree."),
    pause(),
    say(
        "calder",
        "I've also read your first draft of the methods section. There's a mistake I want you to correct. The statistical test you mention is actually appropriate, and you haven't mixed results from different weeks — you haven't got those results yet. The problem is that you describe the site too vaguely. You say 'a campus residence' without saying which building, which floors, or how close it is to the road. A reader couldn't picture it.",
    ),
    pause(),
    say("maya", "We'll tighten that up."),
    pause(),
    say(
        "calder",
        "What should you do next? Some students in your position jump straight to the ethics form, or even visit another campus for a comparison, but I wouldn't do either of those yet. I'd like you to write a short pilot report — even a couple of pages — after you've tested the meters in one room for a single night. Then we'll look at ethics.",
    ),
    pause(),
    say("tom", "A short pilot report. We can do that this week."),
    pause(0.6),
    say(
        "narrator",
        "Before you hear the rest of the discussion, you have some time to look at questions 27 to 30.",
    ),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 27 to 30."),
    pause(0.6),
    say("calder", "Now, you've already run into some problems, haven't you?"),
    pause(),
    say(
        "maya",
        "We have. A few residents refused to take part, which we had to accept. One of the meters didn't stop working, luckily — we tested them all last week. And it wasn't the corridor lights; that was something another group had with a different kind of sensor.",
    ),
    pause(),
    say(
        "tom",
        "The other issue was timing. Two of our planned recording nights clashed with a campus event — there was an all-night open-mic in the courtyard — so those nights would have been completely untypical. You being away in reading week wasn't a problem for us; we just emailed.",
    ),
    pause(),
    say("calder", "So the problems were the refusals, and a clash with a campus event. That's useful to record in the methods."),
    pause(),
    say(
        "calder",
        "Finally, I want to warn you about two possible errors when you analyse the recordings. First, don't place the meters too close to windows — you'll pick up rain and traffic and think it's inside the room. Second, be careful not to treat brief peaks as typical noise. A single slammed door isn't the same as a steady average. Labelling the audio files is important, of course, but you've already set up a naming system, so I'm not worried about that. And you don't need to interview only first-year students — a mix is fine. Weather isn't a major factor indoors here, so I wouldn't lean on a single weather record either.",
    ),
    pause(),
    say("maya", "Windows and brief peaks. We'll watch those."),
    pause(),
    say("calder", "Good. Email me the pilot report when it's ready, and we'll meet again after that."),
    pause(0.6),
    say("narrator", "That is the end of Section 3. You now have 30 seconds to check your answers."),
    gap(CHECK),
]


SECTION4 = [
    say(
        "narrator",
        "Section 4. You will hear a lecture about the life of a nineteenth-century botanical illustrator.",
    ),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 31 to 35."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 31 to 35."),
    pause(0.6),
    say(
        "cole",
        "In this lecture I want to talk about the life of Ada Merrin, a botanical illustrator working in the nineteenth century. She is not as widely known as some of her contemporaries, which is partly why her archive is useful: it hasn't been over-interpreted.",
    ),
    pause(0.5),
    say(
        "cole",
        "Let me begin with her early years. Reference works sometimes say she was born in the market town of Kelworth in eighteen nineteen. In fact, although the family later moved there, Ada was born in a village about four miles to the west. So the correct starting point is a village, not the town.",
    ),
    pause(0.5),
    say(
        "cole",
        "Her father is often described as a doctor, because he later served on a hospital board. That wasn't his profession. He worked as a surveyor, mapping estate boundaries and new roads, and it was on those walks that Ada first learned to look closely at plants.",
    ),
    pause(0.5),
    say(
        "cole",
        "What did she draw first? People assume roses, because a few early watercolours of garden flowers survive. But those came later. Her first drawings were of local ferns, collected in the woods behind the house and labelled with considerable care for a child.",
    ),
    pause(0.5),
    say(
        "cole",
        "Her career began in earnest in eighteen forty-four. One biography claims she was invited to a London studio, and another says she took a teaching post. Neither is right. She was invited to join an expedition to the Andes — a plant-collecting expedition — and she went as the official illustrator.",
    ),
    pause(0.5),
    say(
        "cole",
        "What distinguished her work on that journey, and afterwards, was her insistence on painting plants in their habitat, rather than as cut specimens arranged on a table. Other artists of the period prided themselves on the accuracy of a single leaf against a white background. Merrin wanted the slope, the shade, the neighbouring moss. Habitat, not a studio arrangement, is the key word for her method.",
    ),
    pause(0.6),
    say(
        "narrator",
        "Before you hear the rest of the lecture, you have some time to look at questions 36 to 40.",
    ),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 36 to 40."),
    pause(0.6),
    say(
        "cole",
        "A first book was planned on her return. The publisher did not delay it because of the binding, which was already paid for, nor because of a shortage of subscribers. The delay was the cost of colour — colour printing at the quality she demanded was extremely expensive, and the volume finally appeared five years late.",
    ),
    pause(0.5),
    say(
        "cole",
        "Later in life, in her fifties, she injured her wrist in a fall from a trap, a light horse-drawn carriage, and could no longer work at the same speed. It wasn't her eyesight, which remained sharp, and it wasn't an illness. After the injury to her wrist, she taught illustration to private pupils.",
    ),
    pause(0.5),
    say(
        "cole",
        "She also became a campaigner. She did not campaign for better pay, or for the protection of particular habitats, although she cared about both. She campaigned for women to be admitted to scientific societies, from which they were still routinely excluded.",
    ),
    pause(0.5),
    say(
        "cole",
        "Her final project is sometimes said to have been a guide to seaweeds, because she collected them late in life. She never wrote that guide. The work she did finish, in the last three years of her life, was a guide to mosses, with forty-two plates.",
    ),
    pause(0.5),
    say(
        "cole",
        "Today, gardeners still buy reproductions of her more decorative prints, and a few scientists consult the plates for species that later became rare. But her work is mainly valued by historians, who use her notebooks to reconstruct how field illustration was actually practised.",
    ),
    pause(0.5),
    say(
        "cole",
        "To recap: a village birthplace; a father who was a surveyor; first drawings of ferns; an Andes expedition; plants painted in their habitat; a book delayed by the cost of colour; an injured wrist; a campaign for women; a final guide to mosses; and a reputation now kept alive mainly by historians. I'll stop there, and in the seminar we'll look at two of the plates in more detail.",
    ),
    pause(0.6),
    say("narrator", "That is the end of Section 4. You now have 30 seconds to check your answers."),
    gap(CHECK),
    say(
        "narrator",
        "That is the end of the listening test. In the full test you will now have two minutes to check all your answers.",
    ),
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
