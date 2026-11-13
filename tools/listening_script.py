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
    "marcus": "en-GB-RyanNeural",
    "harriet": "en-GB-LibbyNeural",
    "lena": "en-AU-NatashaNeural",
    "brennan": "en-GB-RyanNeural",
    "jade": "en-GB-MaisieNeural",
    "tomas": "en-AU-WilliamMultilingualNeural",
    "aisha": "en-GB-LibbyNeural",
    "whitby": "en-GB-ThomasNeural",
}

SPEAKER_LABELS = {
    "narrator": "Narrator",
    "marcus": "Marcus",
    "harriet": "Harriet",
    "lena": "Lena Pritchard",
    "brennan": "Dr Brennan",
    "jade": "Jade",
    "tomas": "Tomás",
    "aisha": "Aisha",
    "whitby": "Professor Whitby",
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
    say("narrator", "Section 1. You will hear a telephone conversation between a woman and a receptionist at a community arts centre."),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 1 to 5."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 1 to 5."),
    pause(0.6),
    say("marcus", "Good morning, Elmwood Community Arts Centre, Marcus speaking. How can I help you?"),
    pause(),
    say("harriet", "Oh, hello. I'd like to book a place on one of your weekend pottery workshops, please."),
    pause(),
    say("marcus", "Of course. Let me take a few details. Can I start with your name?"),
    pause(),
    say("harriet", "Yes. It's Harriet Carridge. Sorry — not Carridge. It's Kerridge. That's K-E-R-R-I-D-G-E."),
    pause(),
    say("marcus", "Kerridge. Thank you. And a contact number, in case we have to change anything?"),
    pause(),
    say("harriet", "My mobile is 0 7 7 5 4, 6 2 9 8 1 3. No, wait, I've got that back to front. It's 0 7 7 5 4, 6 2 9 1 8 3."),
    pause(),
    say("marcus", "0 7 7 5 4, 6 2 9 1 8 3. I've got that. Now, the workshops. We still have space on the 18th of May, and there's a later date, the 25th, if you'd rather."),
    pause(),
    say("harriet", "I was hoping for the 11th of May, actually. That's the first Saturday I have free."),
    pause(),
    say("marcus", "I'm afraid the 11th is already full. We keep a short waiting list, but I wouldn't count on a place. The 18th of May is the next one, and that's the one I'd recommend."),
    pause(),
    say("harriet", "That's fine. Please put me down for the 18th of May."),
    pause(),
    say("marcus", "Done. The advertised start time is 2 o'clock, but I should tell you that we actually begin at 2.15. We use the first quarter of an hour for a safety briefing, and we found people were turning up just as that finished. So please arrive by 2.15, not 2 o'clock."),
    pause(),
    say("harriet", "2.15. That's helpful, thank you. And is it a hand-building class? That's what a friend of mine did on a weekday."),
    pause(),
    say("marcus", "The weekday evenings are hand-building, yes. The Saturday workshop is wheel throwing. You get a proper go at the potter's wheel, with a tutor beside you. We don't mix the two on the same day."),
    pause(),
    say("harriet", "Wheel throwing. That's exactly what I wanted."),
    pause(),
    say("narrator", "Before you hear the rest of the conversation, you have some time to look at questions 6 to 10."),
    gap(LOOK),
    say("narrator", "Now listen and answer questions 6 to 10."),
    pause(0.6),
    say("harriet", "Can I just check the price? I thought I saw 29 pounds somewhere."),
    pause(),
    say("marcus", "The concession fee is 29 pounds, but that's only for full-time students and for people over 60. The standard fee is 37 pounds 50. There's also a 45-pound materials deposit on the wall chart, but you can ignore that — we stopped taking a deposit last year."),
    pause(),
    say("harriet", "I'm not a student, and I'm certainly not 60, so it'll be 37 pounds 50 then."),
    pause(),
    say("marcus", "That's right. You can pay when you arrive. Now, what to bring. We supply aprons, and we supply all the clay, so please don't bring your own — it can clog the wheels. The one thing I do suggest is an old shirt, because even with an apron you can get splashes on your sleeves."),
    pause(),
    say("harriet", "An old shirt. Easy enough. Oh, and you asked on the website how people find you. A friend did mention your site, but I didn't actually book from there. I saw a poster in the library and rang you from that."),
    pause(),
    say("marcus", "A library poster. That's useful to know — we've just put those up. A couple of last things. Parking: we do have a small paid car park behind the building, but on Saturdays after 1 p.m. you can park for nothing on Maple Street, right beside the entrance. I'd use that. The supermarket across the road looks convenient, but they only allow their own customers to park there, and they do check."),
    pause(),
    say("harriet", "Maple Street after 1. Perfect. I'll do that."),
    pause(),
    say("marcus", "And just out of interest, is this a one-off, or are you thinking of joining a regular group?"),
    pause(),
    say("harriet", "My sister is the one who loves pottery — it's her birthday soon, and she keeps making bowls. I did think about making her something, but I'm not at that stage. I'm not planning to sell anything either. I really just want to try the wheel and see whether I'd enjoy the Tuesday evening class later in the year."),
    pause(),
    say("marcus", "That's a very good way to start. I'll email your confirmation this afternoon. We look forward to seeing you on the 18th."),
    pause(),
    say("harriet", "Thank you very much. Goodbye."),
    pause(),
    say("marcus", "Goodbye."),
    pause(0.6),
    say("narrator", "That is the end of Section 1. You now have 30 seconds to check your answers."),
    gap(CHECK),
]

SECTION2 = [
    say("narrator", "Section 2. You will hear a welcome talk for visitors at a newly opened coastal visitor centre."),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 11 to 16."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 11 to 16."),
    pause(0.6),
    say("lena", "Good morning, everyone, and welcome to the Saltmarsh Coastal Visitor Centre. My name is Lena Pritchard, and I'm the visitor services officer here. The centre only opened in March, so you're among our first guests, and I'm going to start by walking you through the plan you have in front of you, so you can find your way around."),
    pause(0.5),
    say("lena", "You come in at the south, at the bottom of the plan, past the entrance, and the first building you reach, in the middle of the site, is the main building. That's where the information desk is, and it's already labelled. If you go just to the right of that building, to the east, you'll see a smaller, low structure attached to it. That's the café. It's marked A on your plan. We serve drinks and light meals there until 4 o'clock, and you can sit inside or on the terrace."),
    pause(0.5),
    say("lena", "Directly north of the main building, on the path that leads up towards the water, is a long, low hall. That's the exhibition hall, letter B. It tells the story of the saltmarsh and the people who have worked here, and I do recommend you start there before you walk out to the lagoon."),
    pause(0.5),
    say("lena", "Now, the lagoon itself fills most of the north of the site, at the top of your plan. If you follow the boardwalk — that's already labelled — along the water, you'll come to a small wooden shelter on the north-east shore. That's the bird hide, letter C. It's a quiet place, and we ask you not to use flash photography in there. People sometimes assume the hide is the tall structure on the little spit of land further north, but it isn't. I'll come to that in a moment."),
    pause(0.5),
    say("lena", "Coming back inland, to the west of the main building, there's an open grassy area. That's the picnic lawn, letter D. It's the best place for a packed lunch, and it's more sheltered than it looks. Please don't picnic on the play area just north-west of it — that's already labelled, and it's for children. There's also a first-aid post near the entrance, which is marked on your plan, and the car park is in the south-west corner."),
    pause(0.5),
    say("lena", "Two more outdoor buildings. On the eastern shore of the lagoon, along the path that leaves the exhibition hall, you'll find the boat shed, letter E. That's where we keep the kayaks and the shallow-water boats. And finally, on that narrow spit of land that sticks out into the lagoon at the very north of the plan, there's a slim wooden tower. That's the lookout tower, letter F. You get a wide view of the incoming tide from the top, and, as I said, it isn't the bird hide — the hide is the low shelter to the east."),
    pause(0.6),
    say("narrator", "Before you hear the rest of the talk, you have some time to look at questions 17 to 20."),
    gap(LOOK),
    say("narrator", "Now listen and answer questions 17 to 20."),
    pause(0.6),
    say("lena", "Let me tell you briefly about some of the activities you can join while you're here. First, the guided beach walks. These are popular, and we used to offer them every weekday, but we simply don't have the rangers for that now. They run at weekends only. You don't need to be a member, and you can just turn up at the entrance at 10 o'clock — no booking is required."),
    pause(0.5),
    say("lena", "Kayak hire is a different matter. We have only a small number of kayaks, and for safety we need a staff member on the water with you. So kayak hire must be booked in advance, either at the desk or on the website. It isn't limited to members, and we do hire them on weekdays as well as at weekends, provided a guide is free."),
    pause(0.5),
    say("lena", "If you want a closer look at the wading birds, we lend out telescopes. I should have said we were going to charge a deposit for those, but we dropped that idea. Telescope loans are free with the admission ticket. Just leave your ticket at the desk and collect it when you bring the telescope back. Members don't get any extra privilege there — the same rule applies to everyone."),
    pause(0.5),
    say("lena", "And finally, our evening talks. A few people have asked whether these have been cancelled this season. They have not. What we have done is concentrate them in the summer, when the days are longer and the café can stay open afterwards. So the evening talks run in July and August only. They're included in a separate small fee, and they're open to visitors as well as members."),
    pause(0.5),
    say("lena", "That's all I wanted to cover this morning. Please come and find me if you have any questions, and enjoy your visit to Saltmarsh."),
    pause(0.6),
    say("narrator", "That is the end of Section 2. You now have 30 seconds to check your answers."),
    gap(CHECK),
]

SECTION3 = [
    say("narrator", "Section 3. You will hear a tutor, Dr Brennan, and three students, Jade, Tomás and Aisha, discussing a research project on food waste in a university cafeteria."),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 21 to 26."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 21 to 26."),
    pause(0.6),
    say("brennan", "Thank you for coming in. You've chosen to follow up last year's study of food waste in the cafeteria, which is a good idea, but I want to be sure you don't repeat its mistakes. Tomás, you looked at the old data. What was the main problem?"),
    pause(),
    say("tomas", "Well, their laptop did crash at one point, and they had to re-enter some figures, but I don't think they actually lost the file. And Jade noticed they only sampled two weeks, which is short, but they did both weeks properly."),
    pause(),
    say("jade", "Yes, two weeks in November. The real gap, though, is what you pointed out in your notes, Dr Brennan."),
    pause(),
    say("brennan", "Go on."),
    pause(),
    say("jade", "They only collected data at lunchtime. The cafeteria is open for dinner as well, and the amount of waste might be quite different then. So the set is incomplete."),
    pause(),
    say("brennan", "Exactly. The main weakness is that the data were collected at lunchtime only. If you run this again, you must cover the evening service too. Now, how do you want to measure the waste?"),
    pause(),
    say("tomas", "I thought we could weigh the food that never leaves the kitchen — the trays that are prepared and then thrown away unsold. That seemed tidy."),
    pause(),
    say("aisha", "It's tidy, but it doesn't tell us what students actually leave. I'd rather weigh the leftovers on the plates when they come back."),
    pause(),
    say("jade", "I agree with Aisha. The kitchen already has a rough idea about unserved food. The interesting question is what people put on a plate and then don't eat."),
    pause(),
    say("tomas", "Fair enough. Let's do the leftovers on the plates. We can still glance at the unserved trays, but we won't use them as the official measure."),
    pause(),
    say("brennan", "Good. And interviews? Aisha, you wanted to talk to students in the queue."),
    pause(),
    say("aisha", "I thought we might catch them while they're waiting, and I drafted about twenty-five questions so we wouldn't miss anything."),
    pause(),
    say("brennan", "Two problems there. People in a queue are in a hurry, and a long interview will irritate them and give you poor answers. Keep the interviews to no more than ten minutes, and do them at a table, after they've sat down, not in the line. You can cut that list of questions in half."),
    pause(),
    say("aisha", "Ten minutes. I'll trim it."),
    pause(),
    say("brennan", "Who is doing what, practically? The questionnaire, the poster for the fair, contacting the kitchen?"),
    pause(),
    say("aisha", "I'll write the questionnaire, since I'm cutting it down anyway."),
    pause(),
    say("jade", "Then I'll design the project poster. I did the poster for the geography display last term, so I already know the template."),
    pause(),
    say("tomas", "We still need someone to speak to the kitchen manager. I can try, but I haven't met her."),
    pause(),
    say("brennan", "Leave that for now — I may be able to introduce you. Let's talk about where you'll present the findings. The departmental seminar would have been ideal, but those slots are already full this term."),
    pause(),
    say("tomas", "Could we send it to the student journal? They sometimes take short research notes."),
    pause(),
    say("aisha", "They take months to reply. The campus sustainability fair is in May, and they'll give us a stand if we apply this week."),
    pause(),
    say("jade", "That's better. We'll present at the sustainability fair."),
    pause(),
    say("brennan", "Good choice. And what's the thing that still worries you most?"),
    pause(),
    say("tomas", "Borrowing the weighing scales was my worry, but the lab technicians have already said yes."),
    pause(),
    say("jade", "I'm not too concerned about student numbers either. People like being asked about food."),
    pause(),
    say("aisha", "The kitchen staff are the unknown. If they think we're criticising their work, they may not let us stand by the racks and weigh anything. That's what I keep thinking about."),
    pause(),
    say("brennan", "That's a fair concern, and it's the one I'd watch too. I'll help with that introduction. All right, let's assign the remaining tasks."),
    pause(0.6),
    say("narrator", "Before you hear the rest of the discussion, you have some time to look at questions 27 to 30."),
    gap(LOOK),
    say("narrator", "Now listen and answer questions 27 to 30."),
    pause(0.6),
    say("brennan", "You still need a short literature review, an ethics form, a pilot study, and a room to meet in each week. Let's not leave those hanging."),
    pause(),
    say("tomas", "Aisha is better at the reading than I am. Could she do the literature review?"),
    pause(),
    say("aisha", "I've already got the questionnaire and the ethics form in my head. I really can't take the review as well."),
    pause(),
    say("brennan", "Tomás, the review isn't a huge piece of writing. I'd like you to do it. You've already looked at last year's study, so you're halfway there."),
    pause(),
    say("tomas", "All right. I'll write the literature review."),
    pause(),
    say("aisha", "And I will complete the ethics form. I submitted one for my interview project last year, so I know the wording they want."),
    pause(),
    say("brennan", "Good. The pilot study — a short trial in the cafeteria, maybe two days, before the main count. Jade?"),
    pause(),
    say("jade", "Yes, I'll run the pilot study. I can do that in the first week of April, before the main data collection."),
    pause(),
    say("aisha", "And I'll book the meeting room. I pass the office every morning."),
    pause(),
    say("tomas", "Are you sure? Once you start on the ethics form, you usually disappear for a week."),
    pause(),
    say("aisha", "That's true. I might be chasing signatures. Tomás, could you book the meeting room instead? You're in that building on Tuesdays anyway."),
    pause(),
    say("tomas", "Yes, I'll book the meeting room. Leave it with me."),
    pause(),
    say("brennan", "Excellent. Email me the plan by Friday, and we'll meet again after the pilot."),
    pause(),
    say("jade", "Thank you, Dr Brennan."),
    pause(0.6),
    say("narrator", "That is the end of Section 3. You now have 30 seconds to check your answers."),
    gap(CHECK),
]

SECTION4 = [
    say("narrator", "Section 4. You will hear a lecture about a peatland restoration project on the Fenmere Levels."),
    pause(0.5),
    say("narrator", "First, you have some time to look at questions 31 to 40."),
    gap(LOOK),
    say("narrator", "Now listen carefully and answer questions 31 to 40."),
    pause(0.6),
    say("whitby", "Good afternoon. In this lecture I want to examine a restoration project on the Fenmere Levels, a lowland peat landscape about thirty kilometres from here, and to consider what it can tell us about the wider problem of drying peat soils."),
    pause(0.5),
    say("whitby", "Let me begin with some background. For centuries the Levels were wet. Farmers cut small ditches by hand to move water short distances, and those early ditches are still visible in places. The real change came in the nineteenth century, when engineers constructed a network of drains — deep, straight channels that carried water off the land and into the river. Once those drains were in place, the peat began to dry."),
    pause(0.5),
    say("whitby", "A dry peat soil has several costs. It blows away as dust in a warm spring, and it no longer holds the cool moisture that neighbouring fields depend on. Most seriously, dried peat releases carbon into the air, as the plant material that was locked up under water begins to break down. That carbon loss is now a measurable part of the region's emissions."),
    pause(0.5),
    say("whitby", "There is a physical cost as well. As the peat dries, the ground shrinks and sinks. I nearly said this had damaged local buildings, and in a few villages garden walls have cracked, but the more serious and widespread damage has been to local roads. Several stretches have had to be rebuilt, and a couple of small bridges have been affected too. When you complete the notes, the word you want for that damaged infrastructure is roads."),
    pause(0.5),
    say("whitby", "Now to the project itself. People often date it to 2011, because that was when the first public report appeared, or even to 2012, when the visitor signs went up. In fact the pumps were switched off in 2009. That is the year the restoration really began, quietly, by allowing water to stay on the land instead of being lifted away."),
    pause(0.5),
    say("whitby", "The pumps have not been used since. Water levels are now controlled by sluice gates, which can be raised or lowered to hold a steady depth across each block of land. That is a gentler and cheaper method than pumping, and it has proved surprisingly precise."),
    pause(0.5),
    say("whitby", "The work has not been without interruption. The Levels are full of geese in winter, and visitors often assume that the geese caused the main delay, because they graze the new shoots. In fact the project had to pause because of nesting lapwings. These birds nest on the bare, wet ground in spring, and a construction team cannot move in beside them. The lapwings, not the geese, were the reason work stopped for two seasons."),
    pause(0.5),
    say("whitby", "Farmers, naturally, wanted to know how they would be paid. An early proposal offered a cash subsidy for every hectare left wet, but that scheme was never adopted. Instead, farmers are compensated with a crop of hay. The wet meadows produce a late, high-quality hay which they can sell on, and that has turned out to be more popular than a cheque, because it keeps them in the farming business."),
    pause(0.5),
    say("whitby", "The wildlife response has been encouraging. Otters were expected to return, and they have done so, along the main channels. The unexpected arrival has been eels. Nobody had recorded eels on the Levels for nearly forty years, and they appeared in the second summer after the pumps stopped. That is the species to note as unexpected."),
    pause(0.5),
    say("whitby", "Research is still going on. We already know, as I said, that dry peat releases carbon, so that is not the current question. What the team is measuring now is methane emissions. A wet peatland can give off methane, and we need to be sure that we are not simply trading one greenhouse gas for another. The early figures are reassuring, but the measurements will continue for several years."),
    pause(0.5),
    say("whitby", "Finally, access for the public. The original plan included a small visitor centre at the eastern car park. That funding was withdrawn last year, and the centre will not be built. What is going ahead is a boardwalk, raised above the wettest ground, so that people can reach the lagoon edge without disturbing the birds or sinking into the peat. If you remember only one planned visitor facility, it should be the boardwalk."),
    pause(0.5),
    say("whitby", "I'll stop there, and in the seminar we'll look at how these lessons are being applied to two other lowland sites."),
    pause(0.6),
    say("narrator", "That is the end of Section 4. You now have 30 seconds to check your answers."),
    gap(CHECK),
    say("narrator", "That is the end of the listening test. In the full test you will now have two minutes to check all your answers."),
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
        # Rough duration: words/150 minutes of speech + silences
        sil = sum(c[1] for c in SECTIONS[sid] if c[0] in {"pause", "gap"})
        print(f"  silences {sil:.0f}s, speech ~{n/150*60:.0f}s, total ~{sil + n/150*60:.0f}s")
