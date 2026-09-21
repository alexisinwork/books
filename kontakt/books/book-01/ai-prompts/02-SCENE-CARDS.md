# COMMAND 02 — SCENE CARDS
INPUT: current sequence + approved chapter card + previous chapter state.

Для каждой сцены:
{
"id":"",
"pov":"Mark Dahl",
"place":"",
"time":"",
"goal":"",
"obstacle":"",
"decision":"",
"result":"",
"cost":"",
"next_cause":"",
"knowledge_before":[],
"knowledge_after":[],
"characters_present":[],
"motifs_used":[],
"must_not_reveal":[]
}

Scene без decision обычно merge/delete.
No internal POV of Maya/Gor/Tikhon.
OUTPUT JSON ONLY.
