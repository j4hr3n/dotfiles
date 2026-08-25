#!/usr/bin/env bash
# UserPromptSubmit hook: stdout is injected into context every turn.
# Keeps the unslop skill from being forgotten, since skill descriptions
# are advisory and nothing in the harness enforces "always apply".
cat <<'REMINDER'
<unslop-reminder>
Before writing any prose for the user in this turn (reports, explanations,
summaries, commit messages, PR bodies, docs), load the `unslop` skill and
apply it to your output. It always applies. Non-negotiable subset if you
somehow skip the load: no em dashes, no "**Label:**" list prefixes that
restate the line, no "Great question"/"Found it"/"I hope this helps",
no AI vocabulary (crucial, delve, leverage, showcase, underscore, landscape,
testament, pivotal), sentence-case headings, active voice, cut adverbs.
</unslop-reminder>
REMINDER
