# backend/app/rubrics/prompts.py
"""
Prompt templates for grading short answers and code.
These prompts instruct the LLM to return a compact JSON with:
  - score: 0.0 .. 1.0
  - quality: integer 0..5 (higher is better)
  - feedback: short human-readable explanation
Return ONLY valid JSON (no extra commentary).
"""

SHORT_ANSWER_RUBRIC = """
You are an expert DSA grader. Given an `expected_answer` and a student's `answer`,
evaluate correctness and completeness.

Return a JSON object ONLY (no explanation) with keys:
- "score": a number between 0.0 and 1.0 (1.0 = perfect match)
- "quality": integer 0..5 (5 = perfect)
- "feedback": short actionable feedback (1-2 sentences)

Use this rubric:
- 0.0: no understanding
- 0.1-0.4: partial/correct fragmentary
- 0.5-0.7: decent answer but missing important details
- 0.8-0.95: mostly complete (minor omissions)
- 0.96-1.0: perfect

Input:
EXPECTED_ANSWER:
\"\"\"{expected}\"\"\"

STUDENT_ANSWER:
\"\"\"{answer}\"\"\"

Return JSON only.
"""

CODE_RUBRIC_PROMPT = """
You are an experienced software engineering and algorithms grader. You will be given:
- a code submission (source_code),
- language name or id (language_id),
- the list of testcases with (stdin, expected),
- the raw Judge0 test results with stdout/stderr fields.

Your job:
1) Evaluate **correctness**: how many test cases passed (0..1 score).
2) Evaluate **quality**: integer 0..5 considering readability, correctness, edge-case handling, complexity awareness. (5 = production-ready, 3 = acceptable, 1 = incorrect or insecure).
3) Provide succinct feedback for the student highlighting next steps (1-2 sentences) and potential bugs.
4) Provide a minor suggestion to improve performance or readability (one bullet).

Return a JSON object ONLY (no extra commentary) with keys:
- "score": 0.0..1.0 (pass fraction)
- "quality": integer 0..5
- "feedback": string
- "suggestion": string

ENVIRONMENT:
SOURCE_CODE:
\"\"\"{source_code}\"\"\"

TESTCASES:
\"\"\"{testcases}\"\"\"

JUDGE0_RESULTS:
\"\"\"{judge0_raw}\"\"\"

Return JSON only.
"""