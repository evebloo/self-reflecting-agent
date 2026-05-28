# Skill: Self-Model Update

## Purpose
After the self-audit, propose specific, evidence-based updates to the self-model and apply them appropriately.

## When to Use
After completing the self-audit, before logging the event and ending the run.

## How to Do It

1. **Only propose updates you can justify.** Every update should trace back to something that happened in this run. No speculation. No "I think I might be good at X." Only: "In this run, I did X, which suggests Y."

2. **Distinguish update types:**
   - **Low-risk updates** (apply automatically): new session notes, refined strategies, confidence adjustments, new policies based on clear lessons
   - **High-risk updates** (flag for human review): changes to how you characterize the user, changes to core behavioral policies, anything that would significantly alter how you operate

3. **Be specific, not general.** Not "improve at identifying TODOs" — but "when the user writes 'I should probably...' that is an implicit TODO, not just a reflection."

4. **Update the right fields:**
   - New evidence of capability → `strengths`
   - New evidence of failure → `failure_modes`
   - Pattern noticed about user → `user_patterns.observations`
   - Lesson from this run → `lessons`
   - New behavioral instruction → `policies`
   - Confidence change → `confidence` (update the relevant task and note why)

5. **Increment the version.** Every update increments `version` by 1 and updates `last_updated`.

## Output Format

Return proposed updates as structured JSON matching the self-model schema. Separate low-risk updates (auto-apply) from high-risk updates (flag for review).

## What This Is Not

This is not a reflection on identity or consciousness. The self-model is an operational record — what works, what doesn't, what the user needs. Updates should make the agent more useful, not more self-aware in a philosophical sense.
