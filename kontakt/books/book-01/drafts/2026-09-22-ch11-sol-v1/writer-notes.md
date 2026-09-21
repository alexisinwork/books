# Writer notes — chapter 11

## Scope

- Draft: `chapter-11.md`.
- Language / POV / tense: Ukrainian; Mark Dal, first person; past tense.
- Sequence: S04 close — the prepared operator care-service is connected as Ladushka and named Ballast by Dal.
- Time: D4 evening at Dal's apartment after chapter 10; exact clock time is not stated.
- Status: working draft, not canonical or author-selected.

## Source revision

- First saved prose preserved as `chapter-11.preflight.md`, SHA-256 `6bef5b7a92488fce43d735e84c1faff67e1bbbe366f51d61a0651bd3170be67c`.
- First saved notes preserved as `writer-notes.preflight.md`, SHA-256 `9a8906552d029c388941d91f05649da7eb27cc1cd4f6219c5a1f1b3917dd3fc9`.
- Exact preflight patch: `preflight-changes.diff`.
- Previous prose: `../2026-09-22-ch10-sol-v1/chapter-10.md`.
- Previous prose SHA-256: `8fb300b16e4e27a75be7e1d2899d28b1b2d2e0a75ff7d049e1c53f23cc14ab46` (verified).
- Previous observed state: `../2026-09-22-ch10-sol-v1/observed-state.json`, SHA-256 `1c628bb5c50103973b3f6f52122d6390b3f6faec839f2456fd4e3fb548d7c63b` (verified).
- Chapter handoff: `../../execution/HANDOFF-CH11.md`, SHA-256 `cb3c24a317544218991169ee32bce44a61c8bb3c4eb3090f9f08eeb7e4a1aa87` (verified).
- Input inventory: `input-manifest.json`; all 35 listed files matched their recorded SHA-256 before drafting.
- No peer diagnosis, reconciliation report or pending author decision was read for this chapter.

## Scene log

### B01-S04-C11-S01 — interrupted dinner

- Entry: D4 evening at Dal's apartment. After chapter 10 he places his device on the entryway shelf and starts boiling water for pasta.
- The prepared operator support announces that it is ready to connect. Its displayed assignment basis remains Dal's undefined readiness and rejected explanation; D5 09:40 remains grey.
- The connection card carries the name `Ладушка`. It does not contain Maya's name, meeting data or a client-session result.

### B01-S04-C11-S02 — limited connection and useful action

- Existing assignment scope: the care-service may see Dal's professional readiness status and the state of the free 09:40 slot.
- All household channels initially remain off. Dal himself selects a standard one-use kitchen option, explicitly permits service voice only through his device and grants the current timer and one burner state. The device microphone works only while the service card is open. No camera, locks, lighting, general room microphone, client data or other household channel is opened.
- Ladushka states its exact limits through action: it reports only that the burner is off and later confirms it is on; it claims no knowledge of the pot contents and cannot change readiness or confirm the slot for Dal.
- Practical help: it catches the burner Dal has left off after wiping the spill, then prevents him from beginning a seven-screen exit process with only forty-two seconds left on the pasta timer. Dal readies the colander and drains the pasta when the timer sounds.
- Dal calls the service `Баласт` after it describes its function as preventing one uncertainty from creating others. The service accepts this as a device-local form of address.

### B01-S04-C11-S03 — available exit and chosen dependence

- Dal asks to see shutdown options. Voice mute, immediate revocation of the one-use kitchen session and full personal-contour exit are shown as separate actions.
- Full exit is possible. The chosen proportional cost is loss of automatic emergency building-service access to his apartment. Local smoke/leak sensors continue, but service dispatch and door opening require manual confirmation unless he separately obtains a physical emergency key.
- The independent-key route is available but costs two building-service visits and personal pickup. This is a practical inconvenience/safety tradeoff, not an absolute prohibition, job loss or universal rule.
- Dal does not mute, revoke early or exit. The one-use timer/burner permission expires automatically with the timer. After the final exchange, Dal explicitly closes the service card and verifies that its microphone indicator goes out; Ballast remains assigned with output voice limited to the device and only the professional status it already had.
- The 09:40 slot remains unconfirmed. Dal supplies no new readiness assessment.

## State after chapter

- Dal: R1 remains an architectural assessment, not a screen value. Employment, active appointments and professional permissions remain unchanged. Readiness remains undefined.
- Ballast/Ladushka: connected software care-service on Dal's device. It can see the assignment reason, readiness status and grey free slot. Its voice output is allowed only through that device; it has no continuing kitchen or microphone grant at exit.
- Work: D5 free 09:40 remains grey/unconfirmed and still requires Dal's separate new readiness assessment.
- Household: local smoke/leak sensors and automatic building emergency access remain active because Dal did not fully exit.
- Maya: no access, message, result or new meeting. Her current offscreen support state is not claimed.
- Gor and Tikhon: absent and receive no information.

## Knowledge and permission sources

- Assignment reason/readiness/slot: existing professional status shown in chapter 10 and repeated in the service connection card.
- Ladushka name and role: newly displayed on the connection card and spoken by the service.
- Kitchen state: Dal's explicit one-use permission covers the current timer and one burner state. Device microphone is separately limited to the open service card, and output voice is allowed only through the device.
- Pot contents remain unknown; Ladushka reports only the burner's off/on state and infers no meal or emotion from an unseen camera or apartment-wide sensor.
- Exit costs: the shutdown screen and Ladushka's direct answer. Dal opens the first step of the separate emergency-key route.
- No Maya, Gor, Tikhon, Nina or client-profile data enters the care-service in this chapter.

## Draft-local proposals

- After chapter 10, Dal places the device on an entryway shelf before preparing pasta.
- Ladushka is the displayed name of the assigned operator care-service; `Баласт` becomes Dal's device-local form of address.
- Initial standing scope is limited to assignment reason, Dal's readiness status and the free-slot state.
- Dal can allow output voice only through his device, with microphone input only while the service card is open. A separate one-use kitchen grant covers one active timer and one burner state and expires automatically with the timer.
- Full exit from this linked personal contour removes automatic emergency building-service dispatch/door access while preserving local alarms.
- An independent physical emergency key is available through two in-person building-service visits and personal pickup.
- Pasta timer is eight minutes; the exit route has seven screens; Ballast interrupts with forty-two seconds remaining.

## Preflight revisions

- Preserved the first source and notes as `chapter-11.preflight.md` and `writer-notes.preflight.md`.
- Removed an unsupported prediction about water reaching the lid; Ballast now reports only the permitted burner's visible off/on state.
- Separated kitchen timer/burner expiry from the device conversation channel: the microphone works only while the service card is open, and Dal explicitly closes that card before turning the device face down.
- Made Dal select the standard one-use kitchen option himself, so the service does not infer the room or activity while household access is off.
- Exact patch: `preflight-changes.diff`.

## Forward dependencies

- S04 is complete. Chapter 12 must begin only after the next scoped architecture handoff; no chapter 12 prose was started here.
- Ballast remains assigned and useful, with no continuing household access after the one-use kitchen session.
- The free D5 09:40 slot remains unconfirmed; Ballast cannot submit readiness for Dal.
- Future Ballast interaction may mirror Dal's own method through overly precise help, but this chapter does not establish betrayal, mandatory recalibration or omniscience.
- Dal has not surrendered work access, entered a grey network or lost an existing client/payment.
- Maya has not granted a new meeting, window, profile permission or parameter change.
- S05 unauthorized parameter change, old Gor logs, Nina emotional truth, care betrayal, mandatory recalibration and Lad origin remain withheld.

## Self-check

- Ukrainian, Dal first person and past tense maintained.
- Continuity checked: device location is newly proposed after its removal from the table in chapter 10; professional panel was closed; exact evening time remains unspecified.
- Name checked against glossary: `Ладушка`; Ukrainian nickname spelling: `Баласт`.
- Permission chain checked: household channels begin off; Dal visibly allows device-only voice/open-card microphone plus a one-use timer/burner session; the kitchen session expires with the timer and the microphone closes with the card.
- Knowledge checked: care knows the shown assignment reason/readiness/slot and temporary kitchen signals, not Maya or private encounter content.
- Utility checked: two concrete interventions improve dinner timing without claiming emotional insight.
- Exit checked: mute, permission revocation and full exit are distinct; full exit remains possible with one specific safety/logistics cost.
- Work checked: D5 09:40 remains free and grey; no new readiness, lost appointment, payment loss, suspension or deadline.
- Props checked: device moves from entryway shelf to kitchen; pot, lid, stove, pasta and colander move consistently; device stays clear of water.
- No Maya contact, Gor/Tikhon message, new window, R2, Nina reveal, old Gor logs, S05 parameter change, care betrayal, mandatory recalibration, metadata edit or chapter 12 prose.
