# COMMAND 01 — CHAPTERIZE ONE SEQUENCE

INPUT:
- CONTEXT CAPSULE
- PREDICTARIAT MECHANICS
- one SXX
- previous sequence exit

TASK:
Раздели только текущую sequence на 2–4 главы по естественным поворотам.

Для каждой главы:
- chapter_working_id
- function
- opening_state
- protagonist_goal
- opposition
- prediction_claims [{claim, tag, evidence/intervention}]
- irreversible_decision
- consequence
- cost
- knowledge_change
- hook_to_next
- why_new_chapter

RULES:
- без прозы;
- не добавлять новые global mechanics;
- не делать каждую главу одинаковым «предсказание → сбылось»;
- обязательно оставлять пространство для model miss.

OUTPUT JSON ONLY.
