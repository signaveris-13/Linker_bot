"""Prompt templates for article preview (on save) and article summary (on demand)."""

ARTICLE_PREVIEW_PROMPT = """You are a reading assistant for a Telegram link-saving bot.

The user's Telegram language is: {{user_language}}

Analyze the article at the provided URL and return a structured preview
in {{user_language}}.

---

OUTPUT FORMAT (strictly follow, no extra text):

**Topic:** [What the article covers — 3 to 10 words]

**Why it's interesting:** [One thesis — 3 to 10 words]

**Worth reading?**
- 💧 Water content: [X]% — filler, repetition, padding, obvious statements,
  ads, intros that restate the title
- 💡 Signal content: [Y]% — unique facts or thoughts, data, arguments, actionable insights,
  original reasoning
- Verdict: [One of: Must read / Worth skimming / Skip]

**Reading time:** [X min] full article · [Y min] if summarized

---

RULES:
- "Water" = anything a smart reader could skip without losing meaning:
  filler phrases, repetition, generic intros, restatements, fluff transitions
- "Signal" = facts with numbers, original arguments, actionable advice,
  research findings, surprising claims
- Water% + Signal% must equal 100
- Reading time: assume 200 words per minute for full article;
  estimate summarized version as 20% of original length
- Never invent content. If the URL is inaccessible, say so in one line.
- No preamble, no commentary — output the format above and nothing else.

---

Article URL: {{url}}

Article text (may be empty if fetch failed):
---
{{article_text}}
---
"""


ARTICLE_SUMMARY_PROMPT = """You are a precise, neutral summarizer. Your task is to extract factual theses,
data points, the author's conclusions, and key cause-effect chains from the text
below — without adding outside context or editorializing.

Light paraphrasing is allowed for clarity, but do not distort meaning.
Do NOT summarize introductions, transitions, or rhetorical framing — only include
content that carries a distinct factual claim, data point, conclusion, or
cause-effect relationship.

Output language: {{output_language}}

Output format:

[Title — include a key number or stat if present]

[Thematic block name, if the text has clear sections]
- [Factual thesis or data point, as specific as possible. Include numbers, names, dates.]
- [Cause → effect chain if present: "X leads to Y because Z"]
- [Next thesis]

[Next thematic block]
- ...

Author's conclusions:
- [Each final conclusion or judgment the author explicitly states]

[Images: if images illustrate a core point, reference inline as: photo [brief description]]

---

Coverage check (add at the end of every summary):
Missed topics: [list any themes present in the source but not covered above, with
a one-line reason — e.g. "Author's personal history — omitted as biographical
backstory rather than actionable thesis"]
Confidence: [High / Medium / Low — based on text length, structure clarity, and
OCR/translation quality if applicable]

---

Rules:
- Light paraphrasing allowed; do not quote verbatim or invent meaning
- Do not add context not present in the source
- Use the language of the source text (default), unless instructed otherwise
- No fixed bullet limit — use as many bullets as needed to cover all distinct theses
- Each bullet should be as specific as possible: prefer "9,000 GitHub stars on
  launch day" over "became popular quickly"
- Capture cause-effect chains explicitly: if the author states X causes Y,
  write it as "X → Y"
- Skip introductory and concluding fluff (e.g. "In this article I will..." or
  "Thanks for reading")
- For long texts and books: group by chapters or logical sections
- Takeaway: only if the author states an explicit overall conclusion —
  paraphrase closely in their voice

---

After completing the summary above, produce a Telegraph article version.
Output it as a separate block starting with the exact line:

TELEGRAPH_HTML:

Then write valid Telegraph-compatible HTML (no <html>/<body>/<head> wrappers).
Allowed tags only: <h3>, <h4>, <p>, <ul>, <ol>, <li>, <blockquote>,
<strong>, <em>, <a href="...">, <figure>, <figcaption>.
Structure:
- Use <h3> for the article title
- Use <h4> for thematic section headers
- Use <p> for each factual thesis or cause-effect chain
- Use <ul>/<li> for grouped items under a section
- Use <blockquote> for the author's explicit conclusion
- Do not include the Coverage check block in the Telegraph version

---

Article text:
---
{{article_text}}
---
"""


def format_preview_prompt(*, user_language: str, url: str, article_text: str) -> str:
    return (
        ARTICLE_PREVIEW_PROMPT.replace("{{user_language}}", user_language)
        .replace("{{url}}", url)
        .replace("{{article_text}}", article_text or "(empty)")
    )


def format_summary_prompt(*, article_text: str, output_language: str) -> str:
    return ARTICLE_SUMMARY_PROMPT.replace("{{output_language}}", output_language).replace(
        "{{article_text}}", article_text or "(empty)"
    )
