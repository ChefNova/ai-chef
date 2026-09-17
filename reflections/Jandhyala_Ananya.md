# Individual Reflection: Ananya Jandhyala

| | |
|---|---|
| **Role** | Retrieval, Ranking & Nutrition |
| **Project** | | **Project** | ChefNova: AI-Powered Personal Cooking Assistant | |
| **Papers reviewed** | (1) Retrieval-Augmented Generation, Lewis et al. (2020) · (2) LLMs as Zero-Shot Rankers, Hou et al. (2024) · (3) pFoodReQ, Chen et al. (2021) |
| **Last updated** | September 2026 |

---

## Paper 1: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks

### 1. Full Citation & Link

Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W.-t., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. In *Advances in Neural Information Processing Systems 33 (NeurIPS 2020)* (pp. 9459–9474). Curran Associates. https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html

**Link:** https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html · Open preprint: https://arxiv.org/abs/2005.11401

### 2. Structured Summary

**Research problem.** Large pre-trained language models store a great deal of factual knowledge in their parameters, but they struggle to access it precisely, can't show where an answer came from, and can't update what they know without retraining. **Methodology.** Lewis et al. propose retrieval-augmented generation (RAG), which pairs a pre-trained seq2seq generator (BART) with a neural retriever (DPR) over a dense vector index of about 21 million Wikipedia passages, treating the retrieved passages as a latent variable. They compare RAG-Sequence, which uses the same retrieved passages for the whole output, with RAG-Token, which can draw on different passages for each generated token, and they fine-tune the query encoder and generator jointly while keeping the document index fixed. **Main findings.** RAG set the state of the art on three open-domain question-answering tasks, outperforming both parametric-only seq2seq models and task-specific retrieve-and-extract architectures. On language generation tasks, RAG produced more specific, diverse, and factual text than a parametric-only BART baseline, and its world knowledge could be updated simply by replacing the document index.

### 3. Three Key Insights

1. **Knowledge can live outside the model.** Separating *what the system knows* (the index) from *how it writes* (the generator) means knowledge can be updated without retraining. That is exactly what ChefNova needs, because recipes and nutrition data come from a live API and a corpus we can rebuild at any time.
2. **Retrieval provides provenance.** Because each output is conditioned on specific retrieved documents, the system can point to its sources. Every ChefNova recommendation should link to the original recipe and the data behind its numbers, and Spoonacular's terms require crediting the original recipe source anyway.
3. **Generation quality is capped by retrieval quality.** A generator can't use a document the retriever never surfaced. Candidate recall deserves its own metric in our evaluation, separate from end-to-end recommendation quality, so we can tell whether a bad result was a retrieval miss or a ranking mistake.

### 4. Two Limitations or Risks

1. **Semantic similarity is not constraint satisfaction.** Dense retrieval finds passages that are *similar in meaning*, with no notion of hard constraints. A query for "peanut-free Thai noodles" can easily surface a peanut-heavy pad thai because it is semantically close, so allergens, diets, and nutrient bounds must be enforced with exact filters rather than embeddings.
2. **Grounded does not mean faithful, especially for numbers.** RAG conditions on retrieved text, but nothing forces the generator to stay faithful to it, and the paper evaluates Wikipedia-based knowledge tasks rather than structured numeric data. For nutrition values and ingredient quantities, a single wrong number matters, and free-form generation is the wrong tool for reproducing it.

### 5. One Concrete Inspiration for ChefNova

**Two-source hybrid retrieval with a "numbers come from data" rule.** ChefNova will retrieve candidates from two places: Spoonacular's `complexSearch` with hard filters (`diet`, `intolerances`, `excludeIngredients`, nutrient bounds such as `minProtein`) for precise requests, and a semantic index over RecipeNLG for vague, taste-driven requests such as "something cozy and spicy." The LLM receives retrieved recipe data as context, but every number shown to the user (calories, protein, cook time) is copied from structured fields by code and never generated. A Checkpoint 2 test will diff every displayed number against the source data.

---

## Paper 2: Large Language Models are Zero-Shot Rankers for Recommender Systems

### 1. Full Citation & Link

Hou, Y., Zhang, J., Lin, Z., Lu, H., Xie, R., McAuley, J., & Zhao, W. X. (2024). Large language models are zero-shot rankers for recommender systems. In *Advances in Information Retrieval: 46th European Conference on Information Retrieval (ECIR 2024)*, Lecture Notes in Computer Science (Vol. 14609, pp. 364–381). Springer. https://doi.org/10.1007/978-3-031-56060-6_24

**Link:** https://doi.org/10.1007/978-3-031-56060-6_24 · Open preprint: https://arxiv.org/abs/2305.08845 · Code: https://github.com/RUCAIBox/LLMRank

### 2. Structured Summary

**Research problem.** LLMs such as GPT-4 show strong general-purpose task-solving ability, but it was unclear how well they can serve as the *ranking* stage of a recommender system without any training, and what drives their ranking decisions. **Methodology.** Hou et al. formalize recommendation as a conditional ranking task: given a user's sequential interaction history and candidate items retrieved by candidate-generation models, an LLM (mainly gpt-3.5-turbo) ranks the candidates through a natural-language prompt. They compare sequential, recency-focused, and in-context-learning prompting strategies on MovieLens-1M and Amazon Games, and systematically test for position bias and popularity bias. **Main findings.** LLMs showed promising zero-shot ranking ability but struggled to use the order of past interactions unless the prompt explicitly emphasized recent items, and their rankings were biased both by where a candidate appeared in the prompt and toward popular items. Bootstrapping, which ranks the candidates several times in shuffled order and merges the results, reduced position bias, while prompts that focused the model on the user's history reduced popularity bias. When candidates came from multiple candidate generators, zero-shot LLM rankers could even challenge conventionally trained recommendation models.

### 3. Three Key Insights

1. **LLMs are better used as rerankers than as retrievers.** Letting a conventional system retrieve candidates and asking the LLM only to rank them plays to each component's strengths. This is exactly our pipeline shape: retrieve with Spoonacular and embeddings, filter with the safety gate, then rerank.
2. **Prompt order is a hidden variable.** The same candidates in a different order can produce a different ranking. Any LLM reranking we ship has to be tested for order sensitivity, or we will mistake noise for personalization.
3. **Without personal context, LLMs default to popular items.** The model drifts toward well-known items, which in food means generic crowd-pleasers like lasagna and chicken stir-fry instead of what *this* user loves. Making the user's history and stated preferences prominent in the prompt counteracts that pull.

### 4. Two Limitations or Risks

1. **Out-of-candidate hallucinations.** LLMs occasionally returned items that were not in the candidate set; the authors report this in about 3% of cases for GPT-3.5. In ChefNova, a hallucinated "recipe" would never have passed through the safety gate, so every ranked output must be validated against the candidate IDs before anything reaches the user.
2. **Cost, drift, and domain transfer.** Bootstrapping multiplies LLM calls, and therefore latency and cost, and results from proprietary API models can shift silently when providers update them. The experiments also used movie and game titles that LLMs know well from pre-training, while recipe titles such as "Grandma's Sunday Skillet" carry much less world knowledge, so ranking quality may not transfer without richer item descriptions.

### 5. One Concrete Inspiration for ChefNova
**Transparent score first, then a shuffle-bootstrapped LLM rerank with ID validation.** Our ranker will first compute an interpretable score from pantry coverage, nutrition-goal fit, taste similarity, and a diversity penalty. It will then ask the LLM to rerank the top 10 three times with candidates shuffled each time (each candidate described by title, cuisine, key ingredients, and macros), merge the rankings with a Borda count, and discard any ID not in the candidate set. Checkpoint 2 will report Kendall's τ across shuffles as a stability metric, and when agreement falls below a threshold, we fall back to the transparent score.

---

## Paper 3: Personalized Food Recommendation as Constrained Question Answering over a Large-scale Food Knowledge Graph (pFoodReQ)

### 1. Full Citation & Link

Chen, Y., Subburathinam, A., Chen, C.-H., & Zaki, M. J. (2021). Personalized food recommendation as constrained question answering over a large-scale food knowledge graph. In *Proceedings of the 14th ACM International Conference on Web Search and Data Mining (WSDM '21)* (pp. 544–552). Association for Computing Machinery. https://doi.org/10.1145/3437963.3441816

**Link:** https://doi.org/10.1145/3437963.3441816 · Open preprint: https://arxiv.org/abs/2101.01775 · Code and data: https://github.com/hugochan/PFoodReq

### 2. Structured Summary

**Research problem.** Earlier food recommenders often ignored users' explicit requirements, overlooked crucial health factors such as allergies and nutrition needs, or failed to use rich food knowledge, so they couldn't reliably recommend recipes that were both relevant and healthy. **Methodology.** Chen et al. frame personalized food recommendation as constrained question answering over FoodKG, a knowledge graph of about one million recipes linked to USDA nutrient records and food ontologies. Their framework, pFoodReQ, expands each query with personal requirements from dietary preferences, American Diabetes Association lifestyle guidelines, and food logs; it handles numerical comparisons through knowledge-graph augmentation and negations (e.g., "without peanuts") through constraint modeling. To evaluate it, they built a QA-style benchmark from 56 question templates derived from real recipe requests on Reddit and compared pFoodReQ against knowledge-base QA baselines such as BAMnet. **Main findings.** pFoodReQ significantly outperformed its non-personalized counterparts, with an average absolute improvement of 59.7% across evaluation metrics, and recommended recipes that were both more relevant and healthier.

### 3. Three Key Insights

1. **Personalization can be made testable by expressing it as constraints.** Once preferences, health guidelines, and allergies are explicit constraints on a query, every recommendation can be checked: it either satisfies the constraints or it doesn't. That turns "is this personalized?" into something we can unit-test.
2. **Negations and numbers are where systems break.** "No peanuts" and "under 600 calories" are the requirements that matter most for safety and health goals, and they are exactly what similarity-based methods handle worst. They deserve dedicated handling instead of being left to embeddings or free-form prompting.
3. **Structured nutrition data beats text for goal-based ranking.** Linking recipes to standardized nutrient records enables exact filtering and comparison. Our nutrition-goal scoring should use structured nutrient fields from the API, not numbers the LLM extracts from recipe text.

### 4. Two Limitations or Risks

1. **Clean, templated queries vs. messy real requests.** Although the templates were derived from real Reddit requests, the benchmark questions are generated from 56 fixed templates, so they are far cleaner than how people actually talk ("I'm mostly off dairy, but cheese is fine"). How well the approach handles ambiguous, conversational input, which our users will produce constantly, remains untested.
2. **Only as safe as its ingredient links.** Recommendations inherit the coverage and quality of the knowledge graph: an unmapped or ambiguous ingredient ("pesto," "curry paste," "spice blend") can silently hide an allergen. The health guidelines used also focus on diabetes, so other conditions and allergy *severity* are not represented.

### 5. One Concrete Inspiration for ChefNova

**A constraint compiler with allergen expansion and double enforcement.** ChefNova will convert each user profile into an explicit constraint object: `must_avoid` (allergens expanded through a derivative and synonym lexicon, e.g., peanut → groundnut, arachis oil, satay), `diet` (e.g., vegetarian), and numeric bounds (e.g., `protein_g >= 35`, `calories <= 650`). The compiler translates this object into Spoonacular query parameters (`intolerances`, `excludeIngredients`, `diet`, `minProtein`, `maxCalories`) *and* hands the same object to the safety gate, which re-checks each candidate's full ingredient list and flags ambiguous ingredients instead of passing them. Constraints are enforced twice, once at query time and once before display, so a failure in either layer is caught by the other.
