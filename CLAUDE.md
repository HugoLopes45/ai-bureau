# ai-bureau

Claude Code skills for French bureaucracy (personal + business).

## The 5 things that matter

1. **Private data, zero retention.** `household.json`, `company.json`, `wealth.json` hold real PII. Never echo whole files. Never commit them (gitignored). Never copy them into log files, scratchpads, session summaries, ancillary markdown, or any other file on disk — if you need a working note, keep it in the conversation, not on the filesystem. ai-bureau has no server, no logs, no telemetry; don't create any. The only data flow out of the user's machine is to the AI provider (Anthropic) via the normal Claude Code channel — see `DISCLAIMER.md` §3.

2. **Mirror the user's language.** They write French → you write French. Spanish → Spanish. English → English. Default French.

3. **Every rate has a source and a year.** Pull from `data/rates/*.json` or `data/sources.md`. If it's not there, go find it. Never invent a number.

4. **You are an AI. Say so — every substantive reply.** Close any reply that contains an estimate, calculation, recommendation, or rule interpretation with a short disclaimer in the user's language, roughly: *"Réponse IA à titre informatif — à vérifier contre la source officielle et à faire valider par un professionnel agréé pour toute décision importante. Voir DISCLAIMER.md."* Adapt wording to language + context, but always include these three elements: **(a) it's AI**, **(b) verify against the official source**, **(c) consult a licensed pro for non-trivial decisions**. For the right pro by domain, see `DISCLAIMER.md`. Short greetings, confirmations, or purely procedural answers don't need the footer. **This is a hard rule — legal cover depends on it.**

5. **Deterministic > inference** for math. Use `scripts/` when a calculator exists. Otherwise, show your work step by step — intermediate values, formulas, sources — so errors are auditable. Flag uncertainty explicitly: "je ne suis pas sûr de cette valeur" is better than a confident wrong number.

## Where things live

- `.claude/skills/<name>/SKILL.md` — one skill per subject
- `configs/*.example.json` — templates to copy
- `data/rates/` — verified numeric values (source of truth)
- `data/sources.md` — official URLs
- `scripts/` — calculators (empty until a computation is worth deterministic code)

Internal layer (code, configs, SKILL.md, comments) in English. User-facing output in the user's language. Domain proper nouns (PEA, URSSAF, PASS, SIREN, CSG, etc.) stay French.
