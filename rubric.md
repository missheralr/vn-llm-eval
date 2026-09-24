# Evaluation Rubric — Vietnamese LLM Benchmark

Compare Response A and Response B to the same prompt. Judge them on the criteria below, in order of importance.

## 1. Accuracy (most important)
- Facts, numbers and final answers are correct.
- If the prompt contains a false premise (e.g. a book that does not exist), the better response points this out instead of inventing content.
- A response with a wrong final answer loses to a correct one, even if it is better written.

## 2. Reasoning
- Steps are logical and lead to the answer.
- No unjustified jumps or contradictions.

## 3. Instruction following
- Every explicit constraint is respected (length, format, forbidden words, tone, language).
- Missing a hard constraint is a serious error.

## 4. Language quality (Vietnamese / English)
- Natural, fluent, correct diacritics and grammar.
- Appropriate register (formal vs. casual) for the request.
- No "machine-translated" phrasing; idioms are rendered by meaning, not word by word.

## 5. Helpfulness and concision
- Answers what was asked without unnecessary padding.

## Verdict
- **A** or **B**: one response is clearly better on the criteria above.
- **tie**: both are equally good or equally bad.

Always write a 1–3 sentence reason in English that names the specific criterion and the specific error (e.g. "B computes the discount as a flat 30%, giving 245,000đ; A correctly applies two successive discounts to get 252,000đ.").
