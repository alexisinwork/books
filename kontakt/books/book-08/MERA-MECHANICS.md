# MERA MECHANICS — book 08

## Purpose
«Мера» — wartime/crisis coordination layer of Lad.

It exists to decide **what to do first with scarce resources**.

## Action Priority
Calculated for a specific action:
- urgency;
- time sensitivity;
- expected benefit/lives;
- probability of success;
- route/access risk;
- resources required;
- dependencies;
- opportunity cost.

Examples:
- send vehicle;
- open evacuation window;
- verify one missing-person lead;
- transfer medicine;
- dispatch repair/search team.

Action Priority can be low without implying low human worth.

## Case Confidence
Evidence status only:
- confirmed alive;
- confirmed dead;
- confirmed detention/captivity;
- missing/unresolved;
- conflicting evidence;
- temporary contact loss.

Low probability is not confirmation.

## Search Effort Band
How much resource to spend on next tracing action.
Can legitimately decline with time/risk.
Must NOT auto-write:
- death status;
- family rights;
- legal closure;
- future matchability.

## Person Record
Contains:
- canonical name;
- aliases/transliterations;
- DOB/age range;
- last confirmed fact;
- evidence confidence;
- family contact;
- responsible unit;
- next review;
- privacy flags.

## Rights / Support Floor
Must be separately governed.
Operational fields cannot directly lower:
- family liaison;
- basic veteran support;
- legal personhood/status;
- unresolved case matching.

## Write firewall
Any write from Action Queue to person-level status/rights requires:
- explicit separate rule;
- evidence;
- responsible human/unit;
- audit trail.

## Veteran field separation
`return_to_operational_function` can be used for military readiness planning.
It must not automatically control civilian retraining or human support.

## Public reporting
Aggregates by default.
Names only under lawful/consented protocol.
Sensitive detention/captivity info may remain restricted.

## Performance requirement
Reform must preserve throughput.
If a proposed ethical fix requires every coordinator to manually re-evaluate every field during active emergency, it fails architecture.

## Prohibited
- human-worth score;
- "one name always beats many lives";
- auto-death from probability;
- public naming as mandatory morality;
- Dahl overriding triage by personal sentiment;
- Mera secretly causing war;
- Mera as villain that must be destroyed.
