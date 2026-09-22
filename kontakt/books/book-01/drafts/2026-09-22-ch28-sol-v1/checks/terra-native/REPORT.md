# Terra native review — CH28

## Invocation

| Field | Value |
|---|---|
| Run ID | `ch28-20260922-sol-v1` |
| Role | `terra` |
| Status | `final` |
| Model | `gpt-5.6-terra native` |
| Source | `kontakt/books/book-01/drafts/2026-09-22-ch28-sol-v1/chapter-28.md` |
| Source SHA-256 | `3958ef4b640508b7dd5750ca531278d80ccf1013f028b1e4440bb9bd9567d689` |
| Reader SHA-256 | `3958ef4b640508b7dd5750ca531278d80ccf1013f028b1e4440bb9bd9567d689` |
| Read scope | 81/81 непорожніх блоків, розділених порожніми рядками: `P00001`–`P00081` |

## Actual scope and limits

This was a scoped reading of the target plus the permitted guidance, **not** a strict target-only reading. The target and the following allowed inputs were read in full:

- `.agents/skills/book-language-review/SKILL.md` — SHA-256 `472df890365cabebc652b868ca62ef90f66f1c8a9fcf7475947038ab4f9294cc`
- `kontakt/books/book-01/execution/HANDOFF-CH28.md` — SHA-256 `cbea92bf8d16c72d3aa9b671d9f10f7168b2dad3379b6775ed4db859559fa433`
- `kontakt/books/book-01/voice.json` — SHA-256 `0daed170751ea9d5c8a7f8fd4bfc06309feb62e0cb0cbb057d0f2e2202c424d7`
- `BOOK_SYSTEM/LANGUAGES/uk/STYLE.md` — SHA-256 `c130bb180b60037a51dec0cfdbb551b3339944bd8ddcc4fe76a8df6855d91ddd`
- `BOOK_SYSTEM/LANGUAGES/uk/NATURALNESS.md` — SHA-256 `a22dce300a430f1fef40358476aa436620d234cafb8ced1082e8e901e3dd14e5`

No other chapter prose, writer notes, checks, ledgers, peer reports, canon, or source-language text was read. Consequently, findings about continuity are confined to what the target itself and the permitted handoff establish. No automated language scan was run; this is a full manual literary and Ukrainian-language read.

Exact final paragraph read:

> Я вийшов у коридор. Двері зачинилися за мною. У сумці більше не було жодного керування її сеансом.

## Overall reading

The scene is legible and emotionally restrained. Dal's first-person voice stays concrete, procedural, and self-limiting: he admits his desired outcome but repeatedly leaves the action to Maia. Maia's questions move the scene rather than merely restating the interface. The two short `Ні` answers after her action preserve uncertainty instead of converting it into relief or reconciliation. The ending physically closes both the visit and Dal's operational access.

The administrative wording is mostly functional rather than deadening: it is the pressure surface against which Maia claims an action of her own. The dialogue consistently keeps `ви`; its directness suits their relation and the scene's consent boundary. No unsupported claim is made here about an originating Russian calque: shared structures or technical phrasing alone do not prove one.

## Findings

### T-01 — `confirmed_defect` · clarity / referent

- **Anchor:** `P00005`: “І повідомлення знову зможе повернутися в схожій ситуації.”
- **Confidence:** high.
- **Effect:** The permitted handoff distinguishes a message delivered once from the emotional mediation that may repeat in a similar context. This sentence makes the message itself the returning agent, so the later distinction between the repeat and the person on the other side is less exact.
- **Minimal correction:** “І посередництво знову може повторитися в схожій ситуації.”
- **Basis:** local semantic precision supported by the permitted handoff, not a claim about source-language influence.

### T-02 — `confirmed_defect` · Ukrainian collocation

- **Anchor:** `P00026`: “Потім провела пальцем до керування постійним станом…”
- **Confidence:** high.
- **Effect:** `провести пальцем до` does not naturally name an untouching, directed gesture toward an interface control. The image becomes mechanically vague.
- **Minimal correction:** “Потім повела пальцем у бік керування постійним станом…”
- **Basis:** Ukrainian action phrasing and spatial clarity; no calque origin is asserted.

### T-03 — `confirmed_defect` · time-label phrasing

- **Anchor:** `P00058`: “Її голосова зупинка спрацювала на 05:42.”
- **Confidence:** high.
- **Effect:** `на 05:42` lacks the noun that identifies a timer mark and can momentarily read like an incomplete prepositional construction.
- **Minimal correction:** “Її голосова зупинка спрацювала на позначці 05:42.”
- **Basis:** local Ukrainian idiom. `о 05:42` would instead suggest clock time, so it is less exact for the displayed counter.

### T-04 — `confirmed_defect` · final-image phrasing

- **Anchor:** `P00081`: “У сумці більше не було жодного керування її сеансом.”
- **Confidence:** medium-high.
- **Effect:** Abstract uncountable `керування` is made into an object located in the bag. The intended final fact—Dal has no remaining means to control her session—is recoverable, but the current phrasing is less idiomatic and weakens the closing image.
- **Minimal correction:** “У сумці більше не було нічого, чим можна було б керувати її сеансом.”
- **Basis:** Ukrainian semantic geometry only; this is not attributed to any source language.

## Deliberate choices retained

- **`P00013`, `P00018`, `P00052`–`P00062`: `preserve_for_function`.** The procedural and bureaucratic register is purposeful. It makes the system visible without letting Dal explain Maia's feeling for her.
- **`P00027`–`P00030`: `preserve_for_function`.** Repetition of `назавжди` and the careful distinction between a present setting and all future choice is the scene's ethical hinge, not redundant exposition.
- **`P00041`–`P00043`: `contextual_style_choice`.** “А решта лишиться моєю” is intentionally open as to whether Maia means silence, fear, or the other person; Dal's stated uncertainty keeps the ellipsis readable.
- **`P00068`–`P00075`: `preserve_for_function`.** The apple and the terse “Добре” do not resolve Maia's position. The restraint matches the chapter's stated refusal to diagnose her relief.
- **`P00078`: `already_correct`.** The omitted first-person subject in “Стілець засунув під стіл” remains recoverable from Dal's past-tense narration and gives the exit a brisk physical cadence.

## Literary and voice assessment

No broader rewrite is indicated by this read. The action has a clear arc: question, refusal to collapse future choice into present choice, Maia's visible confirmation, independent closure, and Dal's loss of controls. The technical result is shown on the page, while the human result remains unresolved. The strongest passages are `P00017`–`P00018`, where Dal refuses to turn non-interference into self-congratulation, and `P00069`–`P00075`, where the dialogue does not falsely treat a system change as an answer to another person.

The review does not assess unprovided preceding or subsequent prose, authorial intent beyond the allowed handoff, canon consistency beyond those stated facts, or whether any proposed minimal correction should be accepted. Those decisions remain with the author.
