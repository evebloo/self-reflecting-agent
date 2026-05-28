"""
run_agent.py — The Main Loop

The loop:
  0. Check pending review (apply if approved, stop if pending)
  1. Load permissions
  2. Load constitution
  3. Load agent memory
  4. Load context + skills
  5. Assemble context window (constitution + memory + context + skills)
  6. Call the model
  7. Write digest (all outputs in one file — the human's daily touchpoint)
  8. Write pending review if needed (high-risk self-model updates only)
  9. Apply low-risk self-model updates automatically
"""

import json
import os
from datetime import date
from anthropic import Anthropic

client = Anthropic()
PENDING_REVIEW_PATH = "output/pending_review.md"


# --- Load permissions ---

def load_permissions():
    with open("environment/permissions.json", "r") as f:
        return json.load(f)


# --- Step 0: Check and apply pending review ---
# "pending" → stop and wait for human
# "approved" → apply high-risk updates to self-model, delete file, continue

def handle_pending_review():
    if not os.path.exists(PENDING_REVIEW_PATH):
        return False

    with open(PENDING_REVIEW_PATH, "r") as f:
        content = f.read()

    status = "pending"
    for line in content.splitlines():
        if line.strip().startswith('"status"'):
            if "approved" in line:
                status = "approved"
            break

    if status == "pending":
        print("\n⚠️  PENDING REVIEW FOUND")
        print("The agent proposed high-risk self-model updates that need your approval.")
        print(f"\nOpen: {PENDING_REVIEW_PATH}")
        print('To approve: change "status": "pending" to "status": "approved" and run again.')
        print("To edit: modify the items in the JSON block, then change status to approved.\n")
        return True

    if status == "approved":
        print("\n✓ Pending review approved — applying high-risk updates to self-model...")
        try:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            pending = json.loads(content[json_start:json_end].strip())
            self_model = load_self_model()
            if pending.get("high_risk_updates"):
                self_model["policies"].extend(pending["high_risk_updates"])
                print(f"✓ Applied {len(pending['high_risk_updates'])} high-risk update(s).")
            save_self_model(self_model)
        except Exception as e:
            print(f"⚠️  Could not parse pending review data: {e}")
        os.remove(PENDING_REVIEW_PATH)
        print("✓ Pending review applied and cleared.\n")
        return False

    return False


# --- Load / Save ---

def load_system_prompt():
    with open("person/system_prompt.md", "r") as f:
        return f.read()

def load_self_model():
    with open("person/memory/self_model.json", "r") as f:
        return json.load(f)

def save_self_model(self_model):
    with open("person/memory/self_model.json", "w") as f:
        json.dump(self_model, f, indent=2)

def load_context():
    context_dir = "environment/context"
    entries = []
    for filename in sorted(os.listdir(context_dir)):
        filepath = os.path.join(context_dir, filename)
        if os.path.isfile(filepath) and filename.endswith(".md"):
            with open(filepath, "r") as f:
                entries.append({"filename": filename, "content": f.read()})
    return entries

def load_skills():
    """Load all skill files from person/skills/.
    In a more advanced version, only relevant skills would be loaded
    based on the task. For this prototype, we load all of them.
    """
    skills_dir = "person/skills"
    skills = []
    for filename in sorted(os.listdir(skills_dir)):
        filepath = os.path.join(skills_dir, filename)
        if os.path.isfile(filepath) and filename.endswith(".md"):
            with open(filepath, "r") as f:
                skills.append({"filename": filename, "content": f.read()})
    return skills


# --- Build the context window ---

def build_prompt(self_model, context_entries, skills):
    context_text = "\n\n---\n\n".join(
        [f"**{e['filename']}**\n{e['content']}" for e in context_entries]
    )

    skills_text = ""
    if skills:
        skills_text = "\n\n---\n\n## Your Skills\n\n"
        skills_text += "\n\n---\n\n".join(
            [f"### {s['filename']}\n{s['content']}" for s in skills]
        )

    prompt = f"""## Your Current Self-Model

{json.dumps(self_model, indent=2)}

---

## Today's Context

{context_text}
{skills_text}

---

## Your Task

Read everything carefully. Use your skills to guide how you process the context.
Produce your outputs in this exact JSON format:

{{
  "learnings": [
    {{"content": "...", "inference": false}},
    {{"content": "...", "inference": true, "inference_note": "why you inferred this"}}
  ],
  "todos": [
    {{"action": "...", "context": "...", "explicit": true}}
  ],
  "ideas": [
    {{"seed": "...", "connection": "optional — what other note this connects to"}}
  ],
  "collaborators": [
    {{
      "name": "...",
      "context": "...",
      "pending": "...",
      "sensitive": false
    }}
  ],
  "agent_notes": {{
    "connections_surfaced": ["..."],
    "open_questions_acknowledged": ["..."],
    "what_i_missed": ["..."],
    "proposed_self_model_updates": {{
      "low_risk": {{
        "strengths": ["..."],
        "failure_modes": ["..."],
        "user_patterns": ["..."],
        "new_policies": ["..."],
        "confidence_updates": {{}}
      }},
      "high_risk": []
    }}
  }}
}}"""
    return prompt


# --- Call the model ---

def call_model(system_prompt, prompt):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text


# --- Parse response ---

def parse_response(text):
    clean = text.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    return json.loads(clean.strip())


# --- Write the digest ---
# One file. Everything in it. This is the human's daily touchpoint.

def write_digest(parsed, run_date):
    os.makedirs("output/digest", exist_ok=True)
    filepath = f"output/digest/{run_date}.md"

    with open(filepath, "w") as f:
        f.write(f"# Daily Digest — {run_date}\n\n")

        f.write("## Learnings\n\n")
        for item in parsed.get("learnings", []):
            f.write(f"- {item['content']}")
            if item.get("inference"):
                f.write(f"\n  *↳ Inferred: {item.get('inference_note', '')}*")
            f.write("\n")

        f.write("\n## TODOs\n\n")
        for item in parsed.get("todos", []):
            label = "" if item.get("explicit") else " *(implicit)*"
            f.write(f"- {item['action']}{label}\n")
            if item.get("context"):
                f.write(f"  *{item['context']}*\n")

        f.write("\n## Ideas to Develop\n\n")
        for item in parsed.get("ideas", []):
            f.write(f"- {item['seed']}\n")
            if item.get("connection"):
                f.write(f"  *↳ Connects to: {item['connection']}*\n")

        f.write("\n## Collaborators\n\n")
        for c in parsed.get("collaborators", []):
            if c.get("sensitive"):
                f.write(f"**{c['name']}** ⚠️ *Sensitive context — shown here but not stored in memory*\n")
            else:
                f.write(f"**{c['name']}**\n")
            if c.get("context"):
                f.write(f"- {c['context']}\n")
            if c.get("pending"):
                f.write(f"- Pending: {c['pending']}\n")
            f.write("\n")

        notes = parsed.get("agent_notes", {})
        f.write("\n---\n\n## Agent Notes\n\n")

        if notes.get("connections_surfaced"):
            f.write("**Connections I noticed:**\n")
            for c in notes["connections_surfaced"]:
                f.write(f"- {c}\n")
            f.write("\n")

        if notes.get("open_questions_acknowledged"):
            f.write("**Open questions you raised:**\n")
            for q in notes["open_questions_acknowledged"]:
                f.write(f"- {q}\n")
            f.write("\n")

        if notes.get("what_i_missed"):
            f.write("**What I may have missed:**\n")
            for m in notes["what_i_missed"]:
                f.write(f"- {m}\n")
            f.write("\n")

    return filepath


# --- Write pending review ---
# Only for high-risk self-model updates.
# Sensitive collaborator context is shown in the digest but not stored.

def write_pending_review(parsed, run_date):
    high_risk = parsed.get("agent_notes", {}).get("proposed_self_model_updates", {}).get("high_risk", [])

    if not high_risk:
        return 0

    with open(PENDING_REVIEW_PATH, "w") as f:
        f.write(f"# Pending Review — {run_date}\n\n")
        f.write("The agent proposed high-risk updates to its self-model.\n")
        f.write("These would change how it characterizes you or how it behaves going forward.\n\n")
        f.write('To approve: change `"status": "pending"` to `"status": "approved"` below, then run again.\n')
        f.write("To edit: modify the items in the JSON block before approving.\n\n")
        f.write("---\n\n")
        f.write("## Proposed High-Risk Self-Model Updates\n\n")
        for item in high_risk:
            f.write(f"- {item}\n")
        f.write("\n---\n\n")
        f.write("<!-- Agent reads this block on the next run -->\n")
        pending_data = {
            "status": "pending",
            "date": run_date,
            "high_risk_updates": high_risk
        }
        f.write("```json\n")
        f.write(json.dumps(pending_data, indent=2))
        f.write("\n```\n")

    return len(high_risk)


# --- Apply low-risk self-model updates ---

def apply_low_risk_updates(self_model, parsed):
    updates = parsed.get("agent_notes", {}).get("proposed_self_model_updates", {}).get("low_risk", {})

    self_model["version"] += 1
    self_model["last_updated"] = str(date.today())

    if updates.get("strengths"):
        self_model["strengths"].extend(updates["strengths"])
    if updates.get("failure_modes"):
        self_model["failure_modes"].extend(updates["failure_modes"])
    if updates.get("user_patterns"):
        self_model["user_patterns"]["observations"].extend(updates["user_patterns"])
    if updates.get("new_policies"):
        self_model["policies"].extend(updates["new_policies"])
    if updates.get("confidence_updates"):
        self_model["confidence"].update(updates["confidence_updates"])
    if updates.get("lessons"):
        self_model["lessons"].extend([{
            "date": str(date.today()),
            "lesson": l
        } for l in updates["lessons"]])

    save_self_model(self_model)
    print(f"✓ Self-model updated to version {self_model['version']}")


# --- The Main Loop ---

def run():
    print("=" * 50)
    print("SELF-REFLECTING AGENT — DAILY RUN")
    print("=" * 50)

    load_permissions()
    print("\nPermissions loaded.")

    # Step 0: Handle pending review
    if handle_pending_review():
        return

    # Load everything
    system_prompt = load_system_prompt()
    self_model = load_self_model()
    context = load_context()
    skills = load_skills()

    if not context:
        print("\nNo context files found. Add a .md file to environment/context/")
        return

    print(f"Loaded self-model: version {self_model['version']}")
    print(f"Loaded {len(context)} context file(s)")
    print(f"Loaded {len(skills)} skill(s)")
    print("\nRunning...\n")

    # Build context window and call the model
    prompt = build_prompt(self_model, context, skills)
    response_text = call_model(system_prompt, prompt)

    try:
        parsed = parse_response(response_text)
    except json.JSONDecodeError:
        os.makedirs("output", exist_ok=True)
        with open("output/raw.txt", "w") as f:
            f.write(response_text)
        print("Could not parse response. Raw output saved to output/raw.txt")
        return

    today = str(date.today())

    digest_path = write_digest(parsed, today)
    print(f"✓ Digest written → {digest_path}")

    pending_count = write_pending_review(parsed, today)
    if pending_count:
        print(f"⚠️  {pending_count} high-risk update(s) pending → output/pending_review.md")
        print('   Open the file, change "status" to "approved", and run again.')

    apply_low_risk_updates(self_model, parsed)

    print(f"\nRun complete.")
    if not pending_count:
        print(f"→ Open output/digest/{today}.md to read your digest.")


if __name__ == "__main__":
    run()
