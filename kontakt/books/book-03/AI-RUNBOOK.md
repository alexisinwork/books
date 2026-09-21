# AI RUNBOOK — Predictariat

Модель исполняет architecture, а не перепридумывает философию свободы воли.

## Постоянный контекст
Всегда передавать:
1. `CONTEXT-CAPSULE.md`
2. `BOOK-03-ARCHITECTURE-LOCK.md`
3. `PREDICTARIAT-MECHANICS.md`
4. `CARRY-IN-FROM-BOOK-02.md`
5. `characters.planned.json`
6. `knowledge.planned.json`
7. `promises.planned.json`
8. `motifs.planned.json`
9. current SXX from `architecture.json`
10. previous chapter/sequence state
11. действующий `voice.json` книги 3

## Pipeline
1. `01-CHAPTERIZE-SEQUENCE.md`
2. `02-SCENE-CARDS.md`
3. `03-ARCH-CHECK.md`
4. `04-WRITE-CHAPTER.md`
5. `05-CONTINUITY.md`
6. `06-REVISE.md` if needed
7. `07-SEQUENCE-RECONCILE.md`
8. `08-BOOK-RECONCILE.md`

## Hard stops
Return `BLOCKED` if:
- plot requires exact prophecy without intervention cause;
- model must know thoughts;
- Dall needs a new Resonance power;
- Osya must make a magically unpredicted move to prove freedom;
- Lotz must become secretly evil to preserve tension;
- Taras is used only to state theme;
- book4 value metric must be fully explained;
- Period of Overload must be revealed.

## Core discipline
Every predictive claim in prose must be tagged in planning as one of:
- OBSERVED_PATTERN
- SHORT_HORIZON_BRANCH
- CONDITIONAL_BRANCH
- INTERVENTION_AMPLIFIED
- SCENARIO_CLASS
- MODEL_MISS

If no tag fits, the prediction is probably too magical.
