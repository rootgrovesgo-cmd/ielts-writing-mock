#!/usr/bin/env python3
"""Original Listening Set C audio cues and readable transcripts.

Speech is written for practice only. It imitates Cambridge-style features
(paraphrase, distractors, a speaker changing their mind) but does not copy
any official or leaked paper.
"""

from __future__ import annotations

# Distinct neural voices (edge-tts). en-GB / en-AU only.
# Narrator matches Sets A and B. Other voices prefer unused catalog names
# (Mia, WilliamNeural); remaining roles use a different assignment from A/B
# because the public en-GB / en-AU list is otherwise exhausted.
VOICES = {
    "narrator": "en-GB-SoniaNeural",
    "callie": "en-GB-MiaNeural",
    "gareth": "en-AU-WilliamNeural",
    "mara": "en-GB-LibbyNeural",
    "keira": "en-GB-MaisieNeural",
    "felix": "en-GB-ThomasNeural",
    "coldwell": "en-AU-NatashaNeural",
}

SPEAKER_LABELS = {
    "narrator": "Narrator",
    "callie": "Callie",
    "gareth": "Gareth",
    "mara": "Mara Ellison",
    "keira": "Keira",
    "felix": "Felix",
    "coldwell": "Professor Rhea Coldwell",
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
    say("narrator", "This is the Academic Listening practice test, Set C."),
    pause(0.7),
    say(
        "narrator",
        "Section 1. You will hear a woman booking a weekend shuttle to a harvest fair.",
    ),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 1 to 5."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 1 to 5."),
    pause(0.6),
    say(
        "callie",
        "Hello, is that the Redford Travel Desk? I'd like to book a seat on the weekend shuttle to the Langridge Harvest Fair.",
    ),
    pause(),
    say(
        "gareth",
        "Yes, this is Gareth. I can book you on the Saturday service. Were you looking at a particular departure?",
    ),
    pause(),
    say(
        "callie",
        "The first bus, please. The website said it leaves at eight thirty.",
    ),
    pause(),
    say(
        "gareth",
        "The website is still showing last year's timetable, I'm afraid. People often arrive for eight thirty and find they've missed it. The first bus actually departs at eight fifteen. There's a later one at nine o'clock, but that's the second departure, not the first.",
    ),
    pause(),
    say("callie", "Eight fifteen. And where's the nearest stop to me? I live just by the railway station."),
    pause(),
    say(
        "gareth",
        "The station stop was closed in March, when the roadworks began. There's also a stop at the retail park, but that's a good twenty-minute walk from where you are. The nearest stop to you now is the hospital gates — that's at the end of Park Road, opposite the outpatients' entrance.",
    ),
    pause(),
    say("callie", "Hospital gates. And where does the shuttle actually go? I thought it terminated at the town square."),
    pause(),
    say(
        "gareth",
        "A lot of people get off at the town square because the cafés are there, but the service itself continues and terminates at the west pavilion. That's the entrance to the fairground, beside the flower display. So the destination you want on the timetable is west pavilion.",
    ),
    pause(),
    say("callie", "West pavilion. What's the service number? A neighbour thought it was fourteen."),
    pause(),
    say(
        "gareth",
        "Fourteen is the weekday commuter service, and that doesn't run at weekends. I nearly quoted that myself. The weekend shuttle is service R twelve — that's the letter R, then twelve.",
    ),
    pause(),
    say("callie", "R twelve. Is there anything earlier if I want to help with the set-up?"),
    pause(),
    say(
        "gareth",
        "Yes. If you need to be there before the stalls open, there's an earlier departure at seven forty. It only starts from the depot, though, not from the hospital gates, so you'd have to make your way to the depot first. There isn't a six-thirty service any more — that was withdrawn last autumn.",
    ),
    pause(),
    say("callie", "Seven forty. That's useful to know."),
    pause(0.6),
    say(
        "narrator",
        "Before you hear the rest of the conversation, you have some time to look at questions 6 to 10.",
    ),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 6 to 10."),
    pause(0.6),
    say("callie", "Could you go through the fares? I wasn't sure about paying cash versus using a travel card."),
    pause(),
    say(
        "gareth",
        "Of course. For a day return leaving before nine thirty in the morning, the cash fare is five pounds eighty. It used to be six fifty last year, but that's been reduced. If you pay with a travel card on that same early service, it's four pounds twenty.",
    ),
    pause(),
    say("callie", "Five pounds eighty cash. And after the morning rush?"),
    pause(),
    say(
        "gareth",
        "The cheaper off-peak day return starts after four o'clock in the afternoon — that's sixteen hundred, not three o'clock. A few people have asked about fifteen hundred, but off-peak begins at sixteen hundred. Cash for that off-peak return is six pounds fifty, and with a travel card it's three pounds twenty-five. Not three fifty — that was the old card rate.",
    ),
    pause(),
    say("callie", "Sixteen hundred, and three twenty-five with the card. Is there a faster option?"),
    pause(),
    say(
        "gareth",
        "There is an express service, which goes via the bypass and skips the town square. That's eight pounds cash, and I'm afraid you can't use a travel card on the express. There's no night service at weekends, before you ask — we only run during the day.",
    ),
    pause(),
    say("callie", "Express, eight pounds. What about a family ticket?"),
    pause(),
    say(
        "gareth",
        "A family ticket is eighteen pounds cash, or fifteen with a travel card, and that includes a programme — the printed guide to the stalls. It doesn't include a meal, and it doesn't cover parking. Just the programme.",
    ),
    pause(),
    say(
        "callie",
        "A programme. Please book me on the eight fifteen from the hospital gates, a cash day return.",
    ),
    pause(),
    say("gareth", "Done. I'll email a confirmation this afternoon."),
    pause(),
    say("callie", "Thank you."),
    pause(0.6),
    say("narrator", "That is the end of Section 1. You now have 30 seconds to check your answers."),
    gap(CHECK),
]


SECTION2 = [
    say(
        "narrator",
        "Section 2. You will hear a welcome talk by the coordinator of a community tool library.",
    ),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 11 to 16."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 11 to 16."),
    pause(0.6),
    say(
        "mara",
        "Good evening, and welcome to Elmwood Tool Library. My name is Mara Ellison, and I coordinate the loans and the workshop. I'm glad so many of you have come along, especially those of you who have only just joined.",
    ),
    pause(0.5),
    say(
        "mara",
        "I want to start with something I learned from last year's loan figures. When I first looked at them, I expected power tools to dominate, as they do in most hire shops. Membership itself has been steady, by the way, not falling, and almost everyone who reserves an item does come in to collect it. What surprised me was that the majority of loans were actually for garden tools — hedge trimmers, spades, that kind of thing — not drills and saws.",
    ),
    pause(0.5),
    say(
        "mara",
        "If you've only just joined, there are a few things you might be tempted to do this evening. You can't book the wood workshop until you've completed a short induction, and the weekend repair classes don't start until next month. The one thing you can do straight away is download the inventory app. It shows what's on the shelves in real time, and you can reserve items from your phone.",
    ),
    pause(0.5),
    say(
        "mara",
        "I also want to mention our insurance provider, because people do ask. The premium isn't particularly low, and they don't offer much in the way of optional extra cover. What did please me, though, was how quickly they processed a claim last autumn, when a borrowed sander was damaged. The replacement was agreed in two days, and the wording of the policy was unusually clear.",
    ),
    pause(0.5),
    say(
        "mara",
        "We have had one practical difficulty with a piece of equipment. It wasn't a battery charger overheating — we replaced those last year — and it wasn't a booking that was recorded twice on the website. The problem was the usage meter on the tile cutter: the reading kept jumping, so we couldn't tell whether the machine was due for a service. We've sent that meter back to the manufacturer.",
    ),
    pause(0.5),
    say(
        "mara",
        "We've already tried putting up posters about return dates, and we did consider posting video tutorials, but those take a long time to produce. Evening drop-in sessions are popular, but we're not expanding those just yet. The next method we're going to try is a locker collection system, so you can pick up reserved tools after we close.",
    ),
    pause(0.5),
    say(
        "mara",
        "A few members have asked about weekend home deliveries. I'm doubtful about that option, not because the van is unreliable — it's fairly new — and not because insurance would refuse to cover a staffed delivery. The reason I'm hesitant is that it would be too expensive to run for the small number of requests we actually receive.",
    ),
    pause(0.6),
    say(
        "narrator",
        "Before you hear the rest of the talk, you have some time to look at questions 17 to 20.",
    ),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 17 to 20."),
    pause(0.6),
    say(
        "mara",
        "Before I finish, a few practical tips, including two things you should not do, however often you see them recommended online. Do oil the blades before you return them; that helps the next member. Do label the borrowed boxes with your membership number, and do photograph any damage when you collect an item. What I would not recommend is storing batteries in a refrigerator. Despite what you may have read, the moisture can damage them. And never tighten a drill chuck with pliers; you'll ruin the jaws. Use the key that's supplied, or just your hand.",
    ),
    pause(0.5),
    say(
        "mara",
        "Finally, the questions people bring to the desk. We do occasionally get asked how donations of tools are valued, and how to volunteer as a fixer, but those come up only a few times a term. How to renew a late loan is almost never asked, because the procedure is printed on the receipt. The two topics people most frequently ask about are whether children can come into the workshop — and the answer is yes, if they're with an adult and wearing closed shoes — and whether safety glasses are provided. They are, in the dispenser by the door.",
    ),
    pause(0.5),
    say(
        "mara",
        "That's all from me. Please collect a membership card on your way out, and I hope we'll see you in the workshop soon.",
    ),
    pause(0.6),
    say("narrator", "That is the end of Section 2. You now have 30 seconds to check your answers."),
    gap(CHECK),
]


SECTION3 = [
    say(
        "narrator",
        "Section 3. You will hear two students discussing a presentation on the conversion of disused textile mills into arts venues.",
    ),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 21 to 25."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 21 to 25."),
    pause(0.6),
    say("keira", "Felix, have you looked at the assessment criteria again? I keep worrying we'll be marked down for the wrong thing."),
    pause(),
    say(
        "felix",
        "I had the same worry. I thought we might fail if we used more than ten slides, or even if we worked as a pair instead of alone. I asked Dr Yarrow, and she said neither of those is a problem.",
    ),
    pause(),
    say(
        "keira",
        "The hard requirement is the primary source. If you don't include at least one — an interview, or an archive document — the assessment is marked as incomplete. Going slightly over the twelve-minute limit just loses a couple of marks; it doesn't fail you.",
    ),
    pause(),
    say("felix", "Right. So we must keep that archive letter in, even if it means cutting a slide."),
    pause(),
    say(
        "keira",
        "Speaking of cutting, I want to drop some of the photographs of the courtyard at Kelmara Mill.",
    ),
    pause(),
    say("felix", "Because of the quality? A few of them are a bit dark. Or has the tutor already seen them?"),
    pause(),
    say(
        "keira",
        "The quality is fine, actually, and Dr Yarrow hasn't seen this set. The problem is they'd take too long to talk through. Three of them show almost the same corner of the yard, and we'd spend minutes repeating ourselves.",
    ),
    pause(),
    say("felix", "That's fair. Let's keep one wide shot and lose the close-ups."),
    pause(),
    say(
        "felix",
        "I'm less comfortable with the construction date. The board outside the mill says eighteen forty, but the archive catalogue says 'circa eighteen forty', and one article even gives eighteen fifty-two.",
    ),
    pause(),
    say(
        "keira",
        "We shouldn't present it as a definite fact, and I don't think we should leave the date out, because the timeline matters for the later conversions. Let's keep it but make it clear it's uncertain — we can say 'around eighteen forty'.",
    ),
    pause(),
    say("felix", "Agreed. A caveat is better than pretending we know."),
    pause(),
    say(
        "felix",
        "I still want to include Kelmara Mill itself as a case study, even though it's the well-known one.",
    ),
    pause(),
    say(
        "keira",
        "Everyone already recognises it. Isn't that a reason to leave it out? And the photographs aren't even our best ones. I don't think Dr Yarrow has written about it, either.",
    ),
    pause(),
    say(
        "felix",
        "I know it's familiar, but that's exactly why I want it in. The audience will already recognise it, and it illustrates the mixed-use model more clearly than the quieter examples. The photos aren't the point.",
    ),
    pause(),
    say("keira", "All right, we'll keep Kelmara as the familiar example."),
    pause(),
    say("keira", "What about the quay warehouse conversion? It's a strong story."),
    pause(),
    say(
        "felix",
        "It hasn't been demolished — it's still in use — and there's plenty of published research. The difficulty, though, is that another seminar group has already taken that building. If we include it, we'll just be repeating their case.",
    ),
    pause(),
    say("keira", "That's a good reason to leave it out. Let's drop the quay warehouse because of the overlap."),
    pause(),
    say("felix", "Agreed."),
    pause(0.6),
    say(
        "narrator",
        "Before you hear the rest of the discussion, you have some time to look at questions 26 to 30.",
    ),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 26 to 30."),
    pause(0.6),
    say("felix", "Can I ask about last term? You said your presentation was criticised, but you never said why."),
    pause(),
    say(
        "keira",
        "I still wince about it. The tutor said my argument was hard to follow — I jumped between examples without signposting. It wasn't that I ran out of time, and I don't think I spoke too quietly. It was the structure.",
    ),
    pause(),
    say("felix", "What did she suggest you do next time?"),
    pause(),
    say(
        "keira",
        "She suggested we start with a research question, and keep coming back to it, so the argument stays in view. She didn't ask for a one-page handout, and she didn't mention rehearsing with a timer, though that might still be wise.",
    ),
    pause(),
    say(
        "felix",
        "That helps. I've also noticed that when people don't know enough about these conversions, they just repeat claims from the promotional websites — visitor numbers, 'award-winning design', that kind of thing — as if those were independent findings.",
    ),
    pause(),
    say("keira", "Yes, instead of checking the planning reports. We should be careful not to do that."),
    pause(),
    say(
        "felix",
        "That's partly why I felt so nervous in the practice seminar. It wasn't that I hadn't finished the slides — they were ready — and the projector was fine. I had to present immediately after a very confident group, and I felt we looked hesitant by comparison.",
    ),
    pause(),
    say("keira", "That would make anyone nervous. You'll be fine on the day."),
    pause(),
    say(
        "keira",
        "One last thing. Why are we comparing the privately funded conversions with the publicly funded ones, rather than, say, mills in two different regions?",
    ),
    pause(),
    say(
        "felix",
        "Because we want to show how the funding source affects the final design — which spaces stay public, which become offices, that kind of thing. It isn't a regional contrast.",
    ),
    pause(),
    say("keira", "Good. I'll redraft the outline tonight and send it over."),
    pause(),
    say("felix", "Thanks. See you in the archive tomorrow."),
    pause(0.6),
    say("narrator", "That is the end of Section 3. You now have 30 seconds to check your answers."),
    gap(CHECK),
]


SECTION4 = [
    say(
        "narrator",
        "Section 4. You will hear a lecture on the conservation of seahorses in a temperate estuary.",
    ),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 31 to 40."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 31 to 40."),
    pause(0.6),
    say(
        "coldwell",
        "Good morning. I'm Professor Rhea Coldwell, and in this lecture I'll be talking about the conservation of seahorses in the Eddow estuary, a temperate inlet on the west coast. I want to look first at habitat and population, then at the main threats, and finally at the protection measures now being put in place.",
    ),
    pause(0.5),
    say(
        "coldwell",
        "Although some older field guides still describe seahorses as open-water fish, in the Eddow estuary they are found mainly in beds of seagrass. They do sometimes cling to seaweed along the edge of the channel, but that is not their usual habitat, and they are rarely seen over bare sand.",
    ),
    pause(0.5),
    say(
        "coldwell",
        "Breeding takes place in late summer. People often assume it is in spring, because that is when many inshore fish spawn, but the surveys show that the peak is late summer, when the water is at its warmest.",
    ),
    pause(0.5),
    say(
        "coldwell",
        "As for numbers, counts reached a historic low in nineteen ninety-six, after a period of poor water quality. They have recovered somewhat since then, but we should be cautious. Population size is difficult to estimate, because the fish camouflage so well against the plants. We can count individuals in a sample square, but scaling up from that is far from straightforward. It is not that they migrate out of the estuary; they simply hide.",
    ),
    pause(0.5),
    say(
        "coldwell",
        "I turn now to threats. The main human pressure is not, as some newspaper reports have claimed, the number of visiting kayaks, and it is not bait-digging, which is already restricted. In particular, dredging of the shipping channel disturbs the sediment and uproots the seagrass itself.",
    ),
    pause(0.5),
    say(
        "coldwell",
        "Seahorses also have predators. Gulls will take one if they come across it near the surface, but that is uncommon. The main predators are certain crabs, which can reach them among the stems. Larger fish take surprisingly few.",
    ),
    pause(0.5),
    say(
        "coldwell",
        "Natural disasters matter as well. Summer droughts can lower the water in the creeks, but the animals are usually able to move with the tide. The serious damage comes from winter storms, which tear up whole patches of seagrass and leave the fish with nowhere to hold on.",
    ),
    pause(0.5),
    say(
        "coldwell",
        "Turning to protection, the first practical step is to recruit a local warden. We cannot fund a full research scientist, and a seasonal volunteer would leave in the autumn. A warden who already lives on the estuary can monitor the beds through the year.",
    ),
    pause(0.5),
    say(
        "coldwell",
        "We also need a physical structure. We plan to build a barrier to keep boats off the shallow beds. A fence was discussed, but it would not survive the tides, and we are not building a wall along the shore. A submerged barrier, marked with buoys, is what we have settled on.",
    ),
    pause(0.5),
    say(
        "coldwell",
        "The programme must also decide what, exactly, to protect. Adult males are already watched during the breeding season, and the seagrass itself is covered by existing habitat rules. It is the juveniles, in the first weeks after they leave the pouch, that are most easily lost, and they now have a formal protection target.",
    ),
    pause(0.5),
    say(
        "coldwell",
        "Finally, public awareness. Leaflets were tried a few years ago, and a page on the council website still exists, but neither changed behaviour very much. A campaign on local radio has been more effective — short interviews in the morning programme, reminding skippers to avoid the marked beds. Visits to schools will come later; they are not the current channel.",
    ),
    pause(0.5),
    say(
        "coldwell",
        "I'll stop there, and in the seminar we can look at how these measures are being evaluated.",
    ),
    pause(0.6),
    say("narrator", "That is the end of Section 4. You now have 30 seconds to check your answers."),
    gap(CHECK),
    say(
        "narrator",
        "That is the end of the Listening test. You now have some time to check your answers.",
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
