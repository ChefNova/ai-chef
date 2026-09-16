# Individual Reflection: Aditya Dilip

| | |
|---|---|
| **Role** | Project Lead · Agent Orchestration & LLM Engineering |
| **Project** | RecipeRAG: An Agentic AI Personal Chef |
| **Papers reviewed** | (1) ReAct, Yao et al. (2023) · (2) InteRecAgent, Huang et al. (2025) · (3) Food Recommender Systems survey, Trattner & Elsweiler (2017) |
| **Last updated** | September 2026 |

---

## Paper 1: ReAct: Synergizing Reasoning and Acting in Language Models

### 1. Full Citation & Link

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. In *International Conference on Learning Representations (ICLR 2023)*. https://arxiv.org/abs/2210.03629

**Link:** https://arxiv.org/abs/2210.03629 · Project page and code: https://react-lm.github.io

### 2. Structured Summary

**Research problem.** Large language models had mostly been studied either as *reasoners* (e.g., chain-of-thought prompting) or as *actors* that generate action plans, but reasoning alone is ungrounded and prone to hallucination, while acting alone lacks the high-level planning needed to track progress and recover from errors. **Methodology.** ReAct prompts a single LLM to interleave free-form reasoning traces ("thoughts") with task-specific actions and the observations those actions return, using only one or two in-context examples. The authors evaluate it on knowledge-intensive tasks (HotpotQA question answering and FEVER fact verification) with a simple Wikipedia API, and on two interactive decision-making benchmarks (ALFWorld and WebShop). **Main findings.** On HotpotQA and FEVER, grounding thoughts in retrieved evidence reduced the hallucination and error propagation seen in chain-of-thought reasoning and produced more interpretable trajectories. The best results came from combining ReAct with chain-of-thought, so the model could use both internal knowledge and external information. On ALFWorld and WebShop, ReAct outperformed imitation-learning and reinforcement-learning methods by absolute success rates of 34% and 10%, respectively.

### 3. Three Key Insights

1. **The loop is the point.** Reasoning decides which tool to call next, and each observation corrects the reasoning; neither half works as well alone. For RecipeRAG, "which recipes fit this person?" must always be answered by calling retrieval, nutrition, and safety tools, never from the model's memory.
2. **Grounding buys trust even when raw accuracy is similar.** On HotpotQA, plain chain-of-thought could score about as well as ReAct alone, but hallucination was its dominant failure mode, whereas ReAct's answers were traceable to retrieved evidence. When a wrong answer could trigger an allergic reaction, traceability is worth more than a small accuracy gain.
3. **Readable traces make agents debuggable and steerable.** Because every step is written out, people can see exactly where an agent went wrong, and the authors show that editing a single thought can steer the agent back on track. We should log the thoughts, actions, and observations behind every recommendation and use them for debugging, evaluation, and user-facing explanations.

### 4. Two Limitations or Risks

1. **Loops and derailment.** The authors note that ReAct can get stuck repeating the same thoughts and actions, and a single uninformative search result can derail the rest of the trajectory. In production, an unbounded loop means unbounded latency and API cost; for us, it would also burn through Spoonacular's limited daily request quota.
2. **A plausible thought is not a safe action.** Reasoning traces show *why* an agent acted, not *whether* that reasoning was correct. The strongest results also depended on a very large model (PaLM-540B) with hand-written few-shot examples, so smaller or different models may be less reliable. Safety-critical rules such as allergen exclusion therefore have to be enforced outside the LLM.

### 5. One Concrete Inspiration for RecipeRAG

**A bounded ReAct loop with tool budgets and replayable traces.** Our orchestrator will run a ReAct-style loop over a small, typed tool set (`get_profile`, `scan_pantry`, `search_recipes`, `check_safety`, `rank_candidates`, `explain`). Each request has hard limits: at most 8 steps and 3 Spoonacular calls, plus a loop detector that stops the run when the same action repeats with identical arguments. Every thought, action, and observation is saved as a JSON trace, which our Checkpoint 2 evaluation harness replays to verify *why* each recipe was recommended.

---

## Paper 2: Recommender AI Agent: Integrating Large Language Models for Interactive Recommendations (InteRecAgent)

### 1. Full Citation & Link

Huang, X., Lian, J., Lei, Y., Yao, J., Lian, D., & Xie, X. (2025). Recommender AI agent: Integrating large language models for interactive recommendations. *ACM Transactions on Information Systems, 43*(4), Article 96. https://doi.org/10.1145/3731446

**Link:** https://doi.org/10.1145/3731446 · Open preprint: https://arxiv.org/abs/2308.16505

### 2. Structured Summary

**Research problem.** Traditional recommender models know a domain's item catalog and user behavior well but can't converse or explain themselves, while general-purpose LLMs converse fluently but lack knowledge of domain-specific catalogs and behavior patterns. **Methodology.** Huang et al. propose InteRecAgent, a framework that uses an LLM as the "brain" and recommender models as tools: an information-query tool, retrieval tools (an SQL tool for *hard conditions* such as price and an item-to-item embedding tool for *soft conditions* such as "similar to X"), and a ranking tool that uses the user's profile. The framework adds a shared candidate bus for passing items between tools, long-term and short-term user profiles with "like," "dislike," and "expect" facets, plan-first execution guided by dynamically retrieved demonstrations, and a reflection step in which a critic LLM checks the results and triggers a retry when they are unsatisfactory. **Main findings.** In evaluations with GPT-4-simulated users on the Steam, MovieLens, and Amazon Beauty datasets, InteRecAgent outperformed general-purpose LLMs as a conversational recommender, with the largest advantages in domains less covered by world knowledge. On Amazon Beauty, most LLMs used alone suffered severe hallucination because item names were long, specialized, and complex. The authors also fine-tuned a 7B LLaMA 2 model (RecLlama) on GPT-4-generated imitation data, and it outperformed several larger models as the agent's brain.

### 3. Three Key Insights

1. **Let the LLM plan and let specialized tools decide.** InteRecAgent keeps catalog knowledge and scoring in dedicated tools and uses the LLM for intent parsing, planning, and dialogue. This maps directly onto RecipeRAG: the LLM should never "know" recipes, because Spoonacular and our recipe index do.
2. **Hard and soft conditions need different machinery.** Explicit demands ("under $100") go to exact database filters, while fuzzy ones ("games like Fortnite") go to embedding similarity. Our version: allergies, diet, and nutrient bounds are hard filters, while "something cozy like my mom's dal" is a soft semantic query.
3. **Pass references, not payloads.** The candidate bus lets tools hand large candidate sets to one another while the LLM sees only what it needs, which keeps prompts short and costs low. Recipes with full ingredient lists and nutrition panels are large, so we need the same pattern.

### 4. Two Limitations or Risks

1. **Simulated users may flatter the system.** The evaluation relies on GPT-4 role-playing users built from interaction histories, and they are likely more consistent and cooperative than real people, so conversational success may be overestimated. Food choices also depend on context such as time, health, and social setting (Trattner & Elsweiler, 2017), which a simulator seeded with past ratings can easily miss.
2. **Plan-first execution can commit to a bad plan.** Planning all tool calls up front saves LLM calls, but if an early tool returns something unexpected (for example, zero candidates after strict filtering), the rest of the plan may no longer make sense. Reflection catches some of these errors, but each retry adds latency and cost. In food, the recovery rule matters: when results come back empty, only *soft* preferences may be relaxed, never allergies or dietary rules.

### 5. One Concrete Inspiration for RecipeRAG

**A recipe candidate bus with a non-negotiable `must_avoid` profile field.** Our tools will share a candidate store keyed by recipe ID: `search_recipes` fills it, `check_safety` removes violations, and `rank_candidates` reorders it, while the LLM sees only IDs and compact summaries. User profiles will adopt InteRecAgent's like/dislike/expect structure, extended with a separate `must_avoid` field for allergens and strict dietary rules. That field changes only after explicit user confirmation and is enforced by deterministic code, never by the LLM. When constraints produce no results, the orchestrator may relax only the `like`/`expect` facets, and it tells the user what it relaxed.

---

## Paper 3: Food Recommender Systems: Important Contributions, Challenges and Future Research Directions

### 1. Full Citation & Link

Trattner, C., & Elsweiler, D. (2017). *Food recommender systems: Important contributions, challenges and future research directions* (arXiv:1711.02760). arXiv. https://doi.org/10.48550/arXiv.1711.02760

**Link:** https://arxiv.org/abs/1711.02760

### 2. Structured Summary

**Research problem.** Food recommenders can help people find meals they want to eat and nourish themselves more healthily, yet food recommendation was relatively under-researched compared with other recommender domains and lacked a consolidated overview. **Methodology.** Trattner and Elsweiler survey the state of the art, covering content-based, collaborative filtering, and hybrid approaches; the role of context; specializations such as group recommendation and health-aware recommendation; and how food recommenders have been evaluated. **Main findings.** Taste prediction for food is achievable but performs worse than in other domains, research has relied mainly on explicit feedback such as ratings and bookmarks, and cold start and data sparsity had not been directly addressed. Evaluation has been almost entirely offline, explanations have been implemented only superficially, and issues such as privacy and robustness were essentially unexplored. The authors call for modeling context and social settings, clearer strategies for healthy recommendation (nutrition-aware algorithms, meal plans, and nudging), standard datasets and baselines, and more online studies with real users.

### 3. Three Key Insights

1. **Food is harder to recommend than most items.** Standard methods perform relatively poorly at predicting taste because eating depends heavily on context, including time, health, social setting, and what is available. This justifies RecipeRAG's use of pantry contents and nutrition goals as first-class signals rather than relying on ratings alone.
2. **Healthiness and preference pull in opposite directions.** Recommending healthier food means recommending items the user may like less, a trade-off the authors compare to balancing accuracy against novelty and serendipity. RecipeRAG should make this trade-off explicit and give the user control over it instead of hiding it inside a single score.
3. **Offline accuracy is not success.** The field lacked online evaluation, beyond-accuracy measures such as novelty and diversity, and meaningful explanations. Our evaluation therefore needs real user studies, diversity metrics, and explanation quality in addition to ranking metrics.

### 4. Two Limitations or Risks

1. **It predates LLMs, agents, and multimodal models.** Published in 2017, the survey's roadmap doesn't address hallucination, prompt injection, tool-using agents, or photo-based pantry understanding. Those are now among our project's central risks and opportunities, so the survey's gap analysis has to be supplemented with recent work.
2. **A narrative overview, not a systematic review.** The survey doesn't describe a reproducible search protocol, so its coverage may reflect the authors' own research community, and it offers few head-to-head quantitative comparisons. It is excellent for framing open problems but weak evidence for choosing a specific algorithm.

### 5. One Concrete Inspiration for RecipeRAG

**"Why this recipe" cards with a goals ↔ comfort dial.** Every recommendation will show a short explanation built only from structured data, such as *"Uses 6 of your 8 ingredients · 38 g protein (95% of your per-meal target) · similar to the Thai curry you loved."* A user-controlled dial will shift the ranking weight between nutrition-goal fit and taste match, making the preference–healthiness trade-off visible and adjustable. This addresses two gaps the survey highlights, superficial explanations and the unresolved health–taste trade-off, and we will test both with real users in the Checkpoint 3 pilot study.

---

## Synthesis: What This Means for My Role

- **Architecture:** a bounded ReAct-style orchestrator (Yao et al., 2023) coordinating typed tools and a candidate store (Huang et al., 2025), where the LLM plans and explains while tools retrieve, filter, and score.
- **Safety boundary:** hard constraints (`must_avoid`, diet) live outside the LLM and are enforced deterministically; the orchestrator may relax only soft preferences.
- **Evaluation stance:** beyond offline accuracy, we measure explanation quality, diversity, and real-user outcomes, in line with the open problems identified by Trattner and Elsweiler (2017).
