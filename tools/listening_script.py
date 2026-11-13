#!/usr/bin/env python3
"""Original Listening Set A audio cues and readable transcripts.

Speech is written for practice only. It imitates Cambridge-style features
(paraphrase, distractors, a speaker changing their mind) but does not copy
any official or leaked paper.
"""

from __future__ import annotations

# Distinct neural voices (edge-tts). en-GB / en-AU only.
VOICES = {
    "narrator": "en-GB-SoniaNeural",
    "naomi": "en-GB-LibbyNeural",
    "fraser": "en-AU-WilliamMultilingualNeural",
    "rowan": "en-AU-NatashaNeural",
    "lila": "en-GB-MaisieNeural",
    "jonah": "en-GB-RyanNeural",
    "ellerby": "en-GB-ThomasNeural",
}

SPEAKER_LABELS = {
    "narrator": "Narrator",
    "naomi": "Naomi",
    "fraser": "Fraser",
    "rowan": "Rowan Hale",
    "lila": "Lila",
    "jonah": "Jonah",
    "ellerby": "Professor Bram Ellerby",
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
    say("narrator", "This is the Academic Listening practice test, Set A."),
    pause(0.7),
    say(
        "narrator",
        "Section 1. You will hear a conversation between a woman and a colleague who is recommending independent bookshops.",
    ),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 1 to 5."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 1 to 5."),
    pause(0.6),
    say(
        "naomi",
        "Fraser, have you got a minute? I want to buy some presents this weekend, and I'd rather go to independent bookshops than one of the big chains. Can you recommend a few?",
    ),
    pause(),
    say("fraser", "Of course. There are three I'd suggest, all quite different from each other."),
    pause(),
    say("naomi", "Great. What's the first one?"),
    pause(),
    say(
        "fraser",
        "Ink and Timber. It's the one opposite the tram stop, so it's easy if you're already in the centre.",
    ),
    pause(),
    say("naomi", "That's convenient. Is that why you like it so much?"),
    pause(),
    say(
        "fraser",
        "The location is handy, I'll give you that, but that's not necessarily why I'd recommend it. What people actually come in for is the poetry — they've built up this remarkably wide poetry section, and that's what the shop is known for.",
    ),
    pause(),
    say("naomi", "Poetry. Okay. Any drawbacks?"),
    pause(),
    say(
        "fraser",
        "It can be noisy because of the trams going past. But they've opened a courtyard at the back, and it's a lovely place if you want to sit and read. You sometimes have to book a table if you plan to work there, and you get a view of the old city wall, but the thing itself is the courtyard.",
    ),
    pause(),
    say("naomi", "Nice. And the second shop?"),
    pause(),
    say("fraser", "Harbour Folio, in the covered market."),
    pause(),
    say(
        "naomi",
        "Is that the second-hand one? I think I went to a second-hand bookshop with a similar name.",
    ),
    pause(),
    say(
        "fraser",
        "You're probably thinking of the place the owner used to work — it was a second-hand shop on Canal Row. Harbour Folio itself is different. Let me just check I've got this right for you: the stock is academic, isn't it? Yes — academic titles, university texts, monographs, that kind of thing.",
    ),
    pause(),
    say(
        "naomi",
        "Academic. Good. My nephew's starting university, but I've also got a teenage niece who likes graphic stuff. Do they have anything for her?",
    ),
    pause(),
    say(
        "fraser",
        "The staff are extremely friendly, and if a title isn't in, they'll take a small deposit and order it. They do keep a limited selection of comics for teenage customers. That doesn't mean the academic shelves are thin — those are as comprehensive as ever. It's just a small comics corner.",
    ),
    pause(),
    say("naomi", "That's helpful. And the third one?"),
    pause(),
    say("fraser", "The last one I'd mention is called The Pellam."),
    pause(),
    say("naomi", "The Pellam? How do you spell that?"),
    pause(),
    say("fraser", "P-E-L-L-A-M. The Pellam. Not Pelham — people often add an H."),
    pause(),
    say("naomi", "P-E-L-L-A-M. Got it."),
    pause(0.6),
    say(
        "narrator",
        "Before you hear the rest of the conversation, you have some time to look at questions 6 to 10.",
    ),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 6 to 10."),
    pause(0.6),
    say("naomi", "So where is The Pellam, exactly? A friend said something about the museum."),
    pause(),
    say(
        "fraser",
        "People often mix it up with the café beside the museum, but that's a completely different place. The Pellam is at the top of a staircase — you go through the arch on Silver Lane and then up. Once you're at the top of the staircase, you can't miss the dark green door.",
    ),
    pause(),
    say("naomi", "At the top of a staircase. And why do you recommend it?"),
    pause(),
    say(
        "fraser",
        "The owner is quite well-known — she used to present a book programme on local radio. And I have to say, the reviews are excellent, from all the local papers and from customers online. All the reviews are very good.",
    ),
    pause(),
    say("naomi", "That's reassuring. Anything unusual about the way they operate?"),
    pause(),
    say(
        "fraser",
        "They've stopped using the cheap imported wrapping. Everything they wrap purchases in is produced by a workshop just outside town, so they only use handmade paper. It sounds like a small thing, but they are quite particular about it.",
    ),
    pause(),
    say(
        "naomi",
        "Handmade paper. Do they have a membership scheme? I thought Ink and Timber charged forty-five pounds.",
    ),
    pause(),
    say(
        "fraser",
        "They do. There's a fifteen-pound deposit if you want them to reserve a first edition, and students can join at a concession rate of twenty pounds. The membership itself, though, is thirty pounds a year.",
    ),
    pause(),
    say(
        "naomi",
        "Thirty. I used to walk past The Pellam and think the rooms looked too small, and a bit pricey.",
    ),
    pause(),
    say(
        "fraser",
        "I thought the same until I went back last month. The prices are fair enough, and as for the space, I'd say the rooms are probably average in size — not tiny at all once you're inside.",
    ),
    pause(),
    say("naomi", "Average. That's all really useful, Fraser. Thank you."),
    pause(),
    say("fraser", "Enjoy your weekend. If you start at Ink and Timber, you can do all three in an afternoon."),
    pause(0.6),
    say("narrator", "That is the end of Section 1. You now have 30 seconds to check your answers."),
    gap(CHECK),
]


SECTION2 = [
    say("narrator", "Section 2. You will hear the leader of a community beekeeping workshop giving a welcome talk."),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 11 to 16."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 11 to 16."),
    pause(0.6),
    say(
        "rowan",
        "Good morning, everyone, and welcome to the Westmere community apiary. My name is Rowan Hale, and I'll be leading today's introductory workshop. I'm delighted so many of you have come, some from quite a distance.",
    ),
    pause(0.5),
    say(
        "rowan",
        "Before we go out to the hives, I want to say a little about why beekeeping is not quite like other outdoor activities people take up. A lot of you have mentioned gardening, or birdwatching, because those can be fitted into a weekend, and several of you remarked that the starter kit is actually cheaper than you expected, which is true, and I'll come back to cost later. But what really sets beekeeping apart is that you're working with a colony that already organises itself. You don't get that kind of social structure when you're growing vegetables or watching birds. That's the distinctive thing.",
    ),
    pause(0.5),
    say(
        "rowan",
        "Now, when inspectors visit a site, they sometimes need to work out how a hive was used in the past. People assume you can tell from the colour of the paint — whether it's been given a fresh coat — or from the material, wood versus the newer polystyrene boxes, or even from the basic shape, which is fairly standard anyway. In fact, inspectors often identify a hive's previous use from the scratch marks left on the landing board, those little grooves where earlier colonies wore the wood away. The paint and the material won't tell you that.",
    ),
    pause(0.5),
    say(
        "rowan",
        "I also wanted to touch on why people join a class like this. A few of you have said you hope to produce honey to sell at the Sunday market, and some are here because a neighbour already keeps bees and made it look straightforward. Those are perfectly good reasons. But a surprising number of people sign up because they want to leave a hive to their children or grandchildren — they see it as something that can be passed on. That longer view is more common than you'd think.",
    ),
    pause(0.5),
    say(
        "rowan",
        "As for what I value most about being a beekeeper myself: children who visit tend to love how messy and unpredictable it can be, and a lot of our retired members tell me they value the physical work — lifting the boxes keeps them active. Those are real benefits, but they aren't what I personally prize most. What I value most is how calming it is. Once you start inspecting a hive, the rest of the day just drops away.",
    ),
    pause(0.5),
    say(
        "rowan",
        "You'll notice other visitors here this morning. Some do arrive with a friend, and a few are in a hurry to try advanced techniques before they've learned the basics. I wouldn't encourage that. The fact is, most of the visitors to the apiary are coming for the first time. They're complete beginners, and today's session is designed with that in mind.",
    ),
    pause(0.5),
    say(
        "rowan",
        "One last reminder before we move. The joining instructions I emailed last week already cover jewellery and tying back long hair, so I won't repeat those now. Later this morning we'll go through how to light the smoker. What I need you to do now, though, is put on the veils that are on the bench behind you. Please don't start the tour without one.",
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
        "rowan",
        "Let me say something about the smoker, which is the piece of equipment you'll hear most about this morning. Someone — I forget who — came up with the first version of it a long time ago. I won't go into the history, and I couldn't tell you exactly when it was invented. What I will explain is what the smoke actually does: it masks the alarm scent the bees release, so they become less defensive. That's its function. Some of you may have read that a smoker is a nuisance to keep at home; it can be awkward, but I'm not going to tell you where to put one. A number of beekeepers, especially in urban settings, use a water spray instead of a smoker, and that works perfectly well with a calm colony. Don't worry about repairing a torn bellows today — we'll look at maintenance another time.",
    ),
    pause(0.5),
    say(
        "rowan",
        "A word, too, about the tools on the table. People sometimes laugh at the names — hive tool, uncapping fork — as if they were invented as a joke, but I wouldn't say the names are hard to remember. And despite what you might have heard, they aren't difficult to hold; even the larger ones are quite light. Some of them, like the scraper, are simply adapted from tools used in other trades, painting or plastering. And some do need to be cleaned after every visit to the apiary, particularly anything that's been inside a hive. There's a rumour that one or two items have gone out of production, but that's not the case — you can still buy everything you see here.",
    ),
    pause(0.5),
    say("rowan", "Right. Veils on, please, and we'll walk down to the first hive."),
    pause(0.6),
    say("narrator", "That is the end of Section 2. You now have 30 seconds to check your answers."),
    gap(CHECK),
]


SECTION3 = [
    say(
        "narrator",
        "Section 3. You will hear two university students discussing research for a presentation on academic burnout.",
    ),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 21 to 26."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 21 to 26."),
    pause(0.6),
    say(
        "lila",
        "Jonah, have you had a chance to go through those papers I sent on academic burnout? We need to agree on what we'll actually argue in the presentation.",
    ),
    pause(),
    say("jonah", "I have, and I've got some thoughts. Shall we start with what's driving the increase?"),
    pause(),
    say(
        "lila",
        "Yes. I think one reason burnout has increased is the sheer number of assessments now. It's continuous — not just a set of exams at the end of the year.",
    ),
    pause(),
    say("jonah", "I think you're right. The assessment load has definitely gone up, and I don't see how students get a break."),
    pause(),
    say("lila", "And commuting? A lot of people live further out than they used to, because of rents near campus."),
    pause(),
    say(
        "jonah",
        "That's true. Longer journeys are leaving people exhausted before they even start work. I'd put that down as a cause as well.",
    ),
    pause(),
    say("lila", "Some of the newspaper articles blame social media."),
    pause(),
    say(
        "jonah",
        "I don't think social media is the main thing. People have been on their phones for years, and the rise in burnout looks more recent than that.",
    ),
    pause(),
    say("lila", "Fair point. What about the new term dates? The university changed those, didn't it?"),
    pause(),
    say(
        "jonah",
        "That change happened years ago. I don't see how it explains an increase that's been reported mainly in the last two or three years.",
    ),
    pause(),
    say(
        "lila",
        "Okay, we'll leave that out. I'd also be tempted to put financial pressure on the list — rents, longer part-time hours.",
    ),
    pause(),
    say(
        "jonah",
        "I'm not sure I'd go that far. Plenty of students have always had money worries. Let's not treat that as a reason for the recent rise.",
    ),
    pause(),
    say("lila", "All right. So we're agreed on the assessment load and the commuting."),
    pause(),
    say("jonah", "Yes."),
    pause(),
    say("lila", "Now, the effects. We have to be careful about what we can actually support with solid evidence."),
    pause(),
    say("jonah", "The review we both read said burnout is linked to higher drop-out rates."),
    pause(),
    say("lila", "That's true — those cohort studies are pretty solid. I'm happy to include that."),
    pause(),
    say("jonah", "Same here. And what about memory? I was unsure at first; some of the early papers were small."),
    pause(),
    say(
        "lila",
        "There's a 2021 study from the York lab that tested working memory under exam conditions. After I looked at that, I changed my mind — the evidence that it reduces short-term memory is actually quite strong.",
    ),
    pause(),
    say("jonah", "Yes, I agree now. That one stands up. We should include it."),
    pause(),
    say(
        "lila",
        "Depression, though... a lot of papers treat burnout and depression as if they were the same thing. The definitions are so vague I wouldn't say we have solid evidence that burnout directly causes it.",
    ),
    pause(),
    say(
        "jonah",
        "Agreed. We can't present that as established. And the claim that it permanently lowers academic grades — the studies contradict each other. One shows a dip, the next doesn't.",
    ),
    pause(),
    say("lila", "Exactly, they're inconsistent. As for group work, my seminar last term fell apart, but that's just one group. We can't treat that as evidence."),
    pause(),
    say("jonah", "No. Anecdotes won't do."),
    pause(),
    say("lila", "Okay. We should also say something about Merrow's threshold model. Have you had a proper look at it?"),
    pause(),
    say(
        "jonah",
        "I have, and I have to say I find it difficult to understand. The way he defines the threshold keeps shifting from chapter to chapter.",
    ),
    pause(),
    say(
        "lila",
        "I find it difficult to understand as well. And I don't think it has much practical relevance. It doesn't tell a student what to do on a Sunday evening when they're exhausted.",
    ),
    pause(),
    say(
        "jonah",
        "That's true — little practical relevance. I'd almost go further: I think the model is misleading, because it implies there's a single point where burnout begins, which isn't how it feels.",
    ),
    pause(),
    say(
        "lila",
        "I'm not sure I'd call it misleading. And I wouldn't say it should be more widely accepted either — not until the evidence is clearer. I did wonder whether it just needs further investigation; he only tested it on medical interns.",
    ),
    pause(),
    say(
        "jonah",
        "Maybe, but I wouldn't put 'needs further investigation' forward as a shared view. We can say it's hard to follow, and that it has little practical use, and leave it there.",
    ),
    pause(),
    say("lila", "Agreed."),
    pause(0.6),
    say(
        "narrator",
        "Before you hear the rest of the discussion, you have some time to look at questions 27 to 30.",
    ),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 27 to 30."),
    pause(0.6),
    say(
        "jonah",
        "When we compare burnout to ordinary stress, I get frustrated. Universities still treat it as a busy week. It isn't taken seriously.",
    ),
    pause(),
    say(
        "lila",
        "I feel the same. It's frustrating that tutors still say everyone gets stressed. I don't think the link between the two is overstated, actually; if anything, people underplay how different they are. And I'm not going to claim there's no cure — that's not a question we can settle in a ten-minute presentation.",
    ),
    pause(),
    say("jonah", "Right. We'll register that frustration, but we won't get into whether a cure exists."),
    pause(),
    say(
        "lila",
        "For the opening, we could start with the statistics on how severe cases can become, or with that study on how the pattern differs for men and women.",
    ),
    pause(),
    say(
        "jonah",
        "Those are useful later. If we start with an example from our own experience — like last term, when we both stopped sleeping before the research methods deadline — people in the room will recognise the situation. That's why I want to open with it.",
    ),
    pause(),
    say(
        "lila",
        "Yes. So the audience sees themselves in it, not so we can dramatise how bad it was, and not to make a point about gender. I'll write that example up.",
    ),
    pause(),
    say("jonah", "Thanks. Now, coping strategies. I think short walks between study sessions are a good strategy."),
    pause(),
    say("lila", "So do I. Some guides say walks are useful because they help you come up with new ideas."),
    pause(),
    say(
        "jonah",
        "I don't buy that — I never get any ideas from walking. I do agree they're a good strategy because they interrupt the cycle before it builds, as you said in your notes.",
    ),
    pause(),
    say("lila", "Exactly. That's the reason we should give. They break the cycle, not because they generate ideas."),
    pause(),
    say(
        "jonah",
        "One last thing I find hard to understand is why working under pressure is considered to be enjoyable. The papers say some students actually like a tight deadline, and that it can be beneficial.",
    ),
    pause(),
    say(
        "lila",
        "I find that difficult to understand too. I don't enjoy pressure at all, even though the research says it can help performance. We should flag that as a puzzle, not as something we feel ourselves.",
    ),
    pause(),
    say("jonah", "Good. I think we have a shape for the presentation now. Shall we meet on Thursday to write the slides?"),
    pause(),
    say("lila", "Thursday works. I'll bring the York paper and the drop-out figures."),
    pause(0.6),
    say("narrator", "That is the end of Section 3. You now have 30 seconds to check your answers."),
    gap(CHECK),
]


SECTION4 = [
    say("narrator", "Section 4. You will hear a lecture on reclaiming urban rooftops."),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 31 to 35."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 31 to 35."),
    pause(0.6),
    say(
        "ellerby",
        "In this lecture I want to consider how cities have begun to reclaim their rooftops — not as leftover space above a building, but as a resource in their own right. I'll start with some historical background, then look at recent improvements, and finally at some practical possibilities for the next decade.",
    ),
    pause(0.5),
    say(
        "ellerby",
        "For much of the nineteenth century, city roofs were largely reserved for chimneys and water tanks, and they attracted little official attention. The difficulties that came later are often traced to a single cause. In the early twentieth century, bitumen became the standard waterproofing material. It was cheap and easy to apply, but it trapped heat and later cracked, and a great many of the leaks, temperature spikes and drainage failures that followed can be attributed to that material. So the source of those later problems, in the view of most historians of the built environment, was bitumen.",
    ),
    pause(0.5),
    say(
        "ellerby",
        "Public concern grew slowly. Then, in 1974, a government survey of industrial and commercial roofs delivered a blunt verdict: the typical inner-city roof was declared sterile. That word — sterile — was deliberate. The surveyors weren't only talking about a lack of plants; they meant a surface that supported no useful activity and no habitat of any kind. The phrase stuck, and it shaped funding decisions for years afterwards.",
    ),
    pause(0.5),
    say(
        "ellerby",
        "Let me now turn to more recent improvements, because the picture today is very different. Planted roofs, once experimental, have become relatively common in parts of northern Europe, and they have brought some surprises. Wildlife surveys expected pigeons, and perhaps the occasional fox using a fire escape. What they did not expect was the appearance of lizards, which have been recorded on planted roofs in several inland cities, well away from their usual habitats. That unexpected sighting has been widely reported.",
    ),
    pause(0.5),
    say(
        "ellerby",
        "There has also been a change in how leftover roof rooms are used. Former lift-motor rooms and top-floor workshops, which used to stand empty, have been converted into studios, and, in other cases, into gyms. The studios tend to get the attention in design magazines, but the conversion into gyms has been just as widespread, particularly in dense residential districts.",
    ),
    pause(0.5),
    say(
        "ellerby",
        "At the city scale, some municipalities have started to plan more ambitiously. The city of Tampere, for example, has announced plans to build a rooftop theatre — a small open-air auditorium on a former department store — and I'll come to their other proposal in a moment, because it belongs with a slightly later set of projects.",
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
        "ellerby",
        "Tampere's second commitment is to display pilot projects — modest, carefully monitored installations that other districts can copy. So: a rooftop theatre, and a public display of pilot projects. A different approach can be seen in Coimbra, where cinemas are created on rooftops every summer. Temporary screens go up in June and come down in early September, and the event has become part of the city's cultural calendar. I mention Coimbra because it shows what can be done with very little permanent structure.",
    ),
    pause(0.5),
    say(
        "ellerby",
        "Finally, I want to look at practical possibilities, some of which are already with us. A surprising number of city schools already have a rooftop playground. That is not a future idea; it is current practice, and the schools that have them report better break-time activity and, interestingly, calmer afternoon lessons.",
    ),
    pause(0.5),
    say(
        "ellerby",
        "Changing eating habits, particularly the demand for fresh salad crops in northern cities, have increased the pressure to grow food much closer to where it is eaten. The old method was to truck lettuce in from rural glasshouses. Instead of relying on that, leafy crops could be produced on roofs by soil beds and electric lamps — the lamps already used in indoor horticulture — or, in future, by robots, meaning small automated arms that plant, thin and harvest without a person standing on the roof all day.",
    ),
    pause(0.5),
    say(
        "ellerby",
        "To recap: the historical problems associated with bitumen; a 1974 verdict that roofs were sterile; unexpected lizards; conversions to studios and gyms; Tampere's theatre and pilot projects; Coimbra's summer cinemas; playgrounds already in use; and a shift from rural glasshouses towards lamps now, and robots later. I'll stop there, and in the seminar we'll look at two case studies in more detail.",
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
