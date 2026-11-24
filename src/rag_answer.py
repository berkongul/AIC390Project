"""Week 3 answers with numbered citations (W3.4).

The answer prompt (prompts/rag_v1.txt) gets the retrieved passages numbered [1]..[k]. Every
store fact must end with the number of its passage. When the passages do not answer the
question, the model must reply with FIXED_RESPONSE, word for word.

check_citations() verifies the reply: either it is exactly FIXED_RESPONSE, or it cites at
least one passage and every cited number exists. A reply that fails is flagged, not hidden.

The customer message and the passages go in the user role, as data. Only the prompt file is
in the system role.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import ROOT  # noqa: E402

PROMPT_VERSION = "rag_v1"
FIXED_RESPONSE = ("I can't find that in our store documents, so I can't confirm it. "
                  "A member of the support team will reply in this conversation.")
CITATION = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")


def system_prompt(version=PROMPT_VERSION):
    return (ROOT / "prompts" / f"{version}.txt").read_text(encoding="utf-8")


def user_message(message, hits):
    passages = "\n\n".join(f"[{n}] {h.chunk.text}" for n, h in enumerate(hits, 1))
    return (f"Store passages:\n{passages}\n\n"
            f"Customer message:\n<customer_message>\n{message}\n</customer_message>")


def check_citations(text, k):
    text = text.strip()
    if text == FIXED_RESPONSE:
        return {"fixed": True, "cited": [], "problems": []}
    cited = sorted({int(n) for group in CITATION.findall(text) for n in group.split(",")})
    problems = []
    if not cited:
        problems.append("no citation and not the fixed response")
    bad = [n for n in cited if not 1 <= n <= k]
    if bad:
        problems.append(f"cites passages that do not exist: {bad}")
    return {"fixed": False, "cited": cited, "problems": problems}


def answer(model, message, hits, version=PROMPT_VERSION):
    """model is week2.Model (or anything with .call(system, user))."""
    text = model.call(system_prompt(version), user_message(message, hits)).strip()
    return {"text": text, **check_citations(text, len(hits)), "prompt": version}
