# TLDR
A proof of concept for a mini agent harness containing a self-reflecting agent: an AI agent that audits its own traces, maintains an explicit self-model, and uses feedback to improve its behavior over time.

# Self-Reflecting Agent

A proof of concept for building a self-reflecting daily context agent, built and documented as part of my *Thinkering* series on [Substack](https://eveblou.com).

This is not a polished product. It's a working prototype I built to explore what it means to design an agent with intention, rather than just prompt one into existence. The full write-up, including the design thinking behind every decision — is here: [Why building agents is a design problem](https://evebl.com).

---

## What It Does

Drop your raw daily notes into a folder. The agent reads them, produces a structured digest, and then audits its own behavior, updating what it knows about itself over time.

Every run produces one file: `output/digest/YYYY-MM-DD.md`

That digest contains:
- **Learnings**. Insights that emerged, with inferences labeled
- **TODOs**. Actions extracted from your notes, labeled or not
- **Ideas to develop**. Seeds worth returning to, with connections surfaced
- **Collaborators**. People mentioned and context around them
- **Agent notes**. What it connected, what it may have missed, what open questions you raised

The agent also updates its self-model after each run, learning your patterns, refining its judgment, improving how it works with you over time.

---

## The Design

This prototype follows a three-layer conceptual model:

- **Brain**. Claude (`claude-sonnet-4-6`), via the Anthropic API. Stateless, general purpose. The reasoning engine.
- **Environment**. The harness. The folder structure, execution loop, permissions, and context. The place the brain operates in.
- **Person**. The agent. The designed identity living inside the environment: purpose, persona, constitution, skills, and memory.

```
self-reflecting-agent/
  person/
    system_prompt.md          ← the constitution — who the agent is
    skills/
      gather_context.md       ← how to read notes and notice connections
      self_audit.md           ← how to review its own behavior after each run
      self_model_update.md    ← how to propose updates to its self-knowledge
    memory/
      self_model.json         ← what the agent knows about itself (evolves over time)
  environment/
    run_agent.py              ← the execution loop
    permissions.json          ← what the agent can and cannot access
    context/                  ← drop your daily notes here (.md files)
  output/
    digest/                   ← one dated file per run: your daily touchpoint
    pending_review.md         ← appears when agent proposes high-risk self-model changes
  .env.example                ← API key template
  requirements.txt
```

The file structure mirrors the conceptual model. Where you put things is a statement about how they relate.

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/evebloo/self-reflecting-agent.git
cd self-reflecting-agent
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Add your Anthropic API key**
```bash
cp .env.example .env
```
Open `.env` and replace `your-api-key-here` with your key from [console.anthropic.com](https://console.anthropic.com).

**4. Add your first context file**

Create a `.md` file in `environment/context/`. Name it anything — the agent reads everything in the folder. Write however you naturally think:

```
## May 28 — notes

Met with Sarah about the hiring pipeline. Rubrics feel outdated.
Need to follow up with Marcus on this.

Interesting observation from the leadership sync today...
```

No formatting required. No TODO labels needed. The agent recognizes actions, ideas, and patterns from the texture of your writing.

**5. Run the agent**
```bash
python environment/run_agent.py
```

**6. Read your digest**
```
output/digest/YYYY-MM-DD.md
```

One file. Everything in it.

---

## The Daily Loop

```
1. Drop your notes → environment/context/your-notes.md
2. Run → python environment/run_agent.py
3. Read → output/digest/YYYY-MM-DD.md
4. If pending_review.md appears → read it, change "status" to "approved", run again
```

The agent handles everything else: self-audit, self-model updates, memory management.

---

## The Pending Review

Occasionally the agent will propose a high-risk update to its self-model. Something that would change how it fundamentally characterizes you or how it behaves going forward. These don't apply automatically.

When this happens, `output/pending_review.md` will appear. Open it, read what the agent wants to change about itself, and if you agree:

1. Change `"status": "pending"` to `"status": "approved"` in the JSON block at the bottom
2. Save the file
3. Run again. The update will be applied and the file cleared

If you disagree, edit the JSON block before approving. Or delete the file to discard.

This is not a review of your notes. It's a review of what becomes permanently true about the agent.

---

## Customizing the Agent

The agent's identity lives in `person/system_prompt.md`. Open it and edit it like a document, no code required.

You can change:
- What it produces and how it structures outputs
- How it relates to you (thinking partner, editor, coach, critic)
- What it refuses to do
- What it flags as sensitive
- How it defines success

The skills in `person/skills/` define how the agent approaches specific tasks. Edit them the same way. Plain English, no code.

---

## What's Next

This prototype is deliberately self-contained. One agent. One folder. One loop.

The natural next step is adding persistent environmental context. Files that give the agent ongoing situational awareness about your world: the people you work with, the projects you're running, how you prefer to work. These would live in `environment/context/` alongside your daily notes.

Beyond that: connecting to the places where your work actually happens like Slack, email, meeting notes, shared drives, and eventually building a shared context layer that multiple agents can read from and write to.

That's a systems problem. But it starts here, with understanding the parts.

---

*Built by [Eve-Marie Blouin-Hudon](https://x.com/eveblou) | Helping you see things differently | I'm an experimental psychologist turned product builder. I think and tinker about behavior, design, technology.)
