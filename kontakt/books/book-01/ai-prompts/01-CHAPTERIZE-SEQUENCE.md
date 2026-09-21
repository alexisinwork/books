# COMMAND 01 — CHAPTERIZE ONE SEQUENCE
INPUT: locked context + одна SXX + exit предыдущей sequence.

TASK: раздели только эту sequence на 2–4 главы по естественным поворотам.

Для каждой главы:
- chapter_working_id
- function
- opening_state
- protagonist_goal
- opposition
- irreversible_decision
- consequence
- cost
- knowledge_change
- hook_to_next
- why_new_chapter

RULES:
- без прозы;
- не делать равномерность самоцелью;
- не добавлять новый reveal;
- следующая глава должна возникать из consequence предыдущей.

OUTPUT JSON ONLY.
