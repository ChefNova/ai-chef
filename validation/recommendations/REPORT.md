# Recipe recommendation evaluation and model tradeoffs

Evaluation date: November 4, 2026. The evaluation includes local ranking checks and 36 live API requests. The live run uses six synthetic pantries, three consecutive attempts per scenario and provider, and the application's provider clients. Evidence: [cases.py](cases.py), [evaluate.py](evaluate.py), [offline results](results.json), and [live results](live-results.json).

## Results

| Measure | Observed | Scope |
| --- | --- | --- |
| Hand-labelled application cases | 14/19 match expected outcomes (73.7%) | Synthetic application checks, not LLM accuracy |
| Core behavior cases | 14/14 pass | Filtering, sorting, overlap labels and parsing on a small corpus |
| Explicit limitation probes | 0/5 pass | Five reproducible open gaps; included in the denominator |
| Local p50 / p95 latency | 0.0147 / 0.0281 ms | 1,900 warm executions; parsing, ranking and comparison only |
| Groq / Gemini live requests | 18 / 18 | Provider calls made independently with fallback disabled |
| Requests with at least one displayed recipe | Groq 3/18, Gemini 12/18 | Includes API errors in the denominator |
| Displayed recipes passing the ingredient and declared-time review | Groq 7/7, Gemini 12/12 | Single review of this sample. Actual cooking time and nutrition remain unverified. |

Timing excludes imports, UI rendering, OCR, network and model inference. This is one Windows/Python 3.14.7 run, not a service benchmark. p50 is the median; p95 uses nearest rank. The raw JSON contains every expected and actual outcome. No saved pantry or key is included.

The full suite reports 188 passed, 1 skipped and 5 expected failures. It includes token-accounting checks for both providers, including Gemini thinking tokens. Expected failures are the five gaps below; strict markers force review when behavior improves. The corpus is deliberately adversarial, not a random sample, so 73.7% must not be presented as production recommendation accuracy.

## Live results

| Metric | Groq GPT-OSS 120B | Gemini 3.5 Flash-Lite |
| --- | ---: | ---: |
| Parsed responses | 4/18 (22.2%) | 12/18 (66.7%) |
| API errors | 14 rate-limit errors | 3 server errors and 3 client errors |
| Requests with at least one displayed recipe | 3/18 (16.7%) | 12/18 (66.7%) |
| Recipes returned / displayed | 11 / 7 | 12 / 12 |
| Returned recipes passing applicable ingredient and declared-time checks | 7/11 | 12/12 |
| Requests displaying three recipes | 2/18 | 0/18 |
| Parsed-response p50 / p95 latency | 4.08 / 5.00 s | 4.69 / 6.39 s |
| All-attempt p50 / p95 latency | 0.10 / 5.00 s | 3.36 / 6.39 s |
| Reported input / billed output tokens | 3,563 / 6,585 | 4,044 / 1,990 |
| Estimated list cost from reported usage | $0.00449 | $0.00619 |

Groq's four parsed responses came from the vegan dinner and vegetarian pasta scenarios. One vegan dinner response gave four recipes with no time estimate. The app correctly removed all four because the scenario had a 20-minute limit. Gemini produced one recipe in each of its 12 parsed responses. All three conflicting-request attempts returned client errors, so that scenario produced no recipe from either provider. These results describe this account and back-to-back request pattern. Groq's all-attempt median reflects fast rate-limit rejections. With 4 and 12 parsed responses, each provider's successful p95 is the slowest response in this sample.

I reviewed the ingredients and steps for the 19 displayed recipes against the scenarios. The displayed vegan recipes used plant-based ingredients, the vegetarian recipes used no listed meat or fish, and the three peanut-avoidance results listed neither peanut nor groundnut. The displayed recipes with a time limit gave a time at or below it. These were checks of the generated text. Several short rice recipes depend on the rice variety or on having cooked rice ready, and some steps assumed an ingredient's preparation. For example, one lentil frittata assumed cooked lentils and listed milk without using it in the instructions. A cooking trial and a second reviewer are needed to verify timing, instruction quality, and the formal Relevant@3 gate. The per-request coverage figures include errors and empty filtered results, so they capture the difference between a compliant displayed recipe and the chance of getting one.

Both providers fell short of the provisional 95% coverage target under this load. Groq returned more options when it succeeded, while Gemini produced a displayable recipe more often in this run. Groq's rate limits prevented a recipe comparison across four scenarios. The observed usage supports the cost estimates above. Failed requests with missing usage metadata are excluded from the estimate.

## Accuracy coverage and failures

The 14 core cases check vegan meat/dairy rejection despite wrong model labels; vegetarian dairy permission and fish rejection; a time boundary and unknown cooking time; case-insensitive avoidance; overlap ordering and all three shopping labels; pantry normalization; fastest, protein and missing-ingredient priorities; protein tie breaking; eggplant versus egg; missing ingredient lists; duplicate rejection; and a valid empty response. Expected titles and applicable scores/statuses are specified independently of the ranking implementation.

| Open probe | Expected | Actual |
| --- | --- | --- |
| Rice stock is zero | Missing Rice; 0%; Almost ready | 100%; Cook now |
| Pantry Chickpeas; recipe Chickpea | 100% overlap | 0% overlap |
| Duck labelled Vegan under Vegetarian filter | Reject | Retain |
| Feta labelled Vegan under Vegan filter | Reject | Retain |
| Avoid peanut; recipe Groundnut oil | Reject | Retain |

Availability currently checks names rather than positive stock. Matching lacks canonical names and aliases. Dietary checks rely on incomplete regexes. These are demonstrated application gaps, not their prevalence in model outputs. Prioritize positive-stock handling, ingredient aliases and a reviewed ingredient taxonomy. Expanding regexes alone cannot establish comprehensive dietary compliance. Recipes also lack required ingredient amounts, so name overlap cannot prove quantity feasibility. Model instructions, diet labels and nutrition values have not been independently validated.

## Model selection

| Role | Model | Decision |
| --- | --- | --- |
| Primary, served by Groq | openai/gpt-oss-120b | Supported production option with low listed token rates and JSON support. This run exposed account rate limits. |
| Lower-cost candidate | Groq openai/gpt-oss-20b | Lower price and higher advertised throughput; quality comparison remains pending |
| Fallback | Gemini gemini-3.5-flash-lite | Existing schema integration and independent provider. Its direct-call coverage was higher in this run. |
| Previous default | llama-3.3-70b-versatile | Removed from the default configuration because developer/free access ended August 16, 2026; enterprise accounts are excepted |

Sources: [Groq production models](https://console.groq.com/docs/models), [deprecation notice](https://console.groq.com/docs/deprecations). The application default and `.env.example` now use GPT-OSS 120B. An explicit `GROQ_RECIPE_MODEL` override is respected and must be updated manually if retired. This is hosted by Groq and needs GROQ_API_KEY, not an OpenAI API key.

Groq continues using JSON object mode with the schema in the prompt. JSON syntax does not guarantee schema fidelity or accurate recipes. Both providers pass through the same local parser and ranker. GPT-OSS supports schema mode, but it is not enabled here. See [Groq structured outputs](https://console.groq.com/docs/structured-outputs).

## Latency tradeoffs

Groq uses a 20-second SDK timeout, zero SDK retries, and a 3,000-token completion limit. Errors, empty content or invalid recipe data may trigger Gemini. Fallback is sequential: elapsed primary attempt + fallback request + local processing. The timeout is not an end-to-end guarantee. Gemini currently has no application-specific timeout here; there is no enforced overall latency budget. More reasoning/output tokens and SDK/provider retry behavior can increase the wait. Shorter output reduces decoding work but risks truncation.

A valid empty list or single recipe is accepted. Gemini is not called simply because few recipes survive filtering. The prompt permits up to four recipes and the UI displays at most three survivors. This explains why diversity/coverage must be measured separately from successful JSON parsing.

Groq advertises approximately 500 tokens/s for 120B and 1,000 for 20B. Vendor throughput excludes request overhead. The live results above measure each provider separately. Combined fallback latency remains unmeasured. [Groq model table](https://console.groq.com/docs/models)

## Cost tradeoffs

Standard uncached text list prices checked November 4, 2026, USD per million tokens:

| Model | Input | Output | Example/request | Example/1,000 |
| --- | ---: | ---: | ---: | ---: |
| Groq GPT-OSS 120B | $0.15 | $0.60 | $0.000660 | $0.66 |
| Groq GPT-OSS 20B | $0.075 | $0.30 | $0.000330 | $0.33 |
| Gemini 3.5 Flash-Lite | $0.30 | $2.50 | $0.002490 | $2.49 |

Sources: [Groq pricing table](https://console.groq.com/docs/models), [Google standard pricing](https://aistudio.google.com/docs/pricing#gemini-3.5-flash-lite). Google includes thinking tokens in billed output. Examples assume 800 input and 900 billed output tokens, not measured usage. Formula: `(input_tokens * input_rate + billed_output_tokens * output_rate) / 1,000,000`.

At this illustrative workload 20B costs half as much as 120B; Gemini costs about 3.77 times as much as 120B. This arithmetic says nothing about quality. If both providers consume the full example budget, the fallback chain totals $0.003150, or $3.15 per 1,000 chains. Failure billing varies; assume neither free nor fully billed failures without evidence. Expected cost is expected primary cost plus fallback probability times expected fallback cost. Free-tier allowances, account limits, caching, taxes and OCR are excluded. This recipe path uses neither batch processing nor search grounding.

## Reproduce the evaluation

From the repository root in PowerShell:

```powershell
.venv/Scripts/python.exe -m validation.recommendations.evaluate
.venv/Scripts/python.exe -m pytest tests -q --tb=short
# Set keys in app/.env or the environment first; this makes billable API calls.
.venv/Scripts/python.exe -m validation.recommendations.evaluate --live --live-repeats 3 --output validation/recommendations/live-results.json
```

For this run, the keys were already configured in `app/.env.example`. The benchmark loaded that file into the process before importing the evaluation module:

```powershell
.venv/Scripts/python.exe -c "from dotenv import load_dotenv; load_dotenv('app/.env.example'); from validation.recommendations.evaluate import main; main()" --live --live-repeats 3 --output validation/recommendations/live-results.json
```

Six synthetic scenarios cover vegan dinner, vegetarian quick meal, peanut avoidance, sparse pantry, protein preference and a conflicting request. Three repeats with both providers make 36 requests. Each provider is tested directly, without fallback hiding failures. No real pantry database is read. The runner records full request latency, parse success, returned/retained/displayed counts, normalized recipes, token metadata and estimated list cost. Keys, provider error messages and raw response bodies are not saved; missing keys produce skipped rows. Unknown model overrides produce null cost rather than the wrong price.

Request timing includes client creation and completion; successful attempts get separate percentiles from all attempts. Small-sample percentiles are exploratory. Compare 20B by setting GROQ_RECIPE_MODEL in a new process and choosing a different output file. Costs use reported input/output token usage; Gemini output adds candidate and thinking tokens. These are standard-list estimates, not invoices.

Two independent reviewers should inspect both raw suggestions and displayed top-three recipes, using the pantry and constraints:

- Constraint compliance: independently compliant displayed recipes / all displayed recipes. Inspect ingredients and instructions, not the app's own filter or model diet label.
- Coverage: attempted requests with at least one independently compliant displayed recipe / all attempted requests, including errors.
- Relevant@3: attempted requests with at least one displayed recipe both reviewers judge practical and responsive / all attempted requests. Retain initial ratings and resolve disagreements.
- Diversity: report distinct meal types and the proportion of requests with three distinct options. One returned recipe is currently allowed.
- Instruction quality: score 0 (unusable), 1 (needs substantial edits), or 2 (clear actionable sequence), with notes on unsupported claims and quantities.

Provisional gates: zero observed hard-constraint violations, at least 80% Relevant@3, and recipes returned successfully on at least 95% of attempted requests. Establish a UI latency target before live evaluation and an enforced deadline before promising it. These are targets, not achieved results. Neither local tests nor a small live sample establish allergy safety or general nutritional accuracy.
