# ChefNova: Project Proposal

**Your AI chef for smarter meals tailored to your pantry, preferences, and diet.**

A conversational cooking assistant grounded in receipt-derived, user-confirmed grocery inventory.

**Team:** Chaitanya Nirantar · Ananya Jandhyala · Aditya Dilip · Prathamesh Mulay  
**Checkpoint 1 · Fall 2026**  
**Length:** 708 words (Sections 1–5, excluding headings and references; whitespace count).

## 1. Problem Significance

ChefNova helps college students, beginner cooks, and people with dietary preferences decide what to cook from groceries they actually have. A student with rice, chickpeas, and spinach may find many recipes, yet still need to check quantities, missing ingredients, preparation time, and substitutions. A grocery receipt records purchases; it cannot establish what remains after cooking or discarding food.

Our hypothesis is that recommendations grounded in user-confirmed inventory and explicit preferences can reduce meal-selection effort. Reduced waste, spending, and preparation time are potential benefits to investigate, not demonstrated outcomes.

Generative AI can interpret abbreviated receipt entries and conversational requests containing several changing constraints. Structured forms and parsers remain useful baselines. ChefNova combines flexible interpretation with database operations, deterministic checks, and user confirmation rather than making the model authoritative about inventory.

## 2. Prior Work & Gaps

The team’s reflections cover ten unique papers. Trattner and Elsweiler (2017) identify challenges involving context, explanations, and real-user evaluation. Yum-me demonstrates preference elicitation combined with nutritional goals (Yang et al., 2017), motivating lightweight conversational preference capture.

pFoodReQ models dietary restrictions, negations, and numerical requirements as explicit constraints (Chen et al., 2021). KERL grounds personalized recipe recommendations in retrieved food knowledge (Mohbat & Zaki, 2025), while retrieval-augmented generation provides a general foundation for conditioning outputs on external evidence (Lewis et al., 2020). These approaches motivate retrieval followed by constraint checking and explanation.

ReAct connects reasoning with tool use (Yao et al., 2023); InteRecAgent coordinates specialized retrieval and ranking tools for interactive recommendations (Huang et al., 2025). Candidate-position and popularity biases in LLM ranking motivate stability checks (Hou et al., 2024).

Inverse Cooking separates ingredient prediction from instruction generation (Salvador et al., 2019), and FoodLMM emphasizes food-specific multimodal tasks and structured outputs (Yin et al., 2025). Their food-image results do not validate receipt parsing. ChefNova therefore investigates receipt-derived quantities, mandatory inventory reconfirmation, and constraint preservation together, without claiming these components are individually novel.

## 3. Proposed Technical Approach

The workflow is: upload a grocery receipt, review extracted items, save quantities, request a recipe, confirm or edit the inventory table, and receive recommendations. Confirmation is required before every recipe recommendation because purchased quantities may become outdated.

The existing local prototype supports PNG/JPG receipt extraction through Gemini and inventory persistence in SQLite. Identical receipt bytes are deduplicated per user; matching item names and units are combined, while different units remain separate. Automatic consumption tracking is outside the initial scope.

The proposed pipeline adds structured conversational constraints, recipe retrieval, deterministic filtering, and ranking. Extraction produces item names, quantities, and units for user correction. Prices must not be interpreted as quantities, and unknown package sizes require clarification. Quantity checks compare recipe requirements with confirmed inventory only when units are compatible; unsupported conversions are flagged. Recommendations identify missing ingredients and link to recipe sources. Explanations use retrieved facts, while persistence and arithmetic remain in code.

## 4. Checkpoint 2 Validation Plan

We will use a fixed evaluation set, document model and prompt versions, and retain structured tool results and error logs.

- **Extraction:** measure item, quantity, and unit accuracy across varied receipt layouts; record corrections per receipt.
- **Constraints:** test multi-turn additions and revisions, measuring violations of explicit exclusions and dietary requirements.
- **Inventory:** verify that every recommendation follows confirmation and that edits affect the next result.
- **Feasibility:** test insufficient quantities, unknown units, missing core ingredients, and proposed substitutions.
- **Recommendation quality:** compare against ingredient matching with explicit filters; assess candidate-order sensitivity, source faithfulness, and meal-selection effort.

Two annotators will label a shared subset and report agreement. The team will define numerical acceptance thresholds before evaluation. Confirmation bypasses and explicit hard-constraint violations are release-blocking failures; other results will include per-metric scores and error analysis.

## 5. Risk Analysis & Mitigation

**Privacy:** Receipts can expose purchase history and identifying details. We will disclose external Gemini processing, use synthetic or redacted demo receipts, and avoid retaining raw images locally. Local profile names do not provide authentication.

**Bias:** We will inspect cuisine variety and candidate-order effects and avoid moralizing language about food or body weight.

**Safety and hallucination:** Dietary filtering is not verified allergy safety. Ambiguous ingredients must trigger clarification; unsuccessful searches must not silently relax hard restrictions. Nutrition values, when available, will be attributed to structured sources rather than presented as model-measured facts. Unknown quantities and uncertain substitutions remain visible. Receipt text will be treated as data, not instructions that can override system rules.

## References

The following ten sources match the reviewed corpus in [literature/BIBLIOGRAPHY.md](../literature/BIBLIOGRAPHY.md).

- Chen, Y., Subburathinam, A., Chen, C.-H., & Zaki, M. J. (2021). Personalized food recommendation as constrained question answering over a large-scale food knowledge graph. In Proceedings of the 14th ACM International Conference on Web Search and Data Mining (WSDM '21) (pp. 544–552). Association for Computing Machinery. https://doi.org/10.1145/3437963.3441816

- Hou, Y., Zhang, J., Lin, Z., Lu, H., Xie, R., McAuley, J., & Zhao, W. X. (2024). Large language models are zero-shot rankers for recommender systems. In Advances in Information Retrieval: 46th European Conference on Information Retrieval (ECIR 2024), Lecture Notes in Computer Science (Vol. 14609, pp. 364–381). Springer. https://doi.org/10.1007/978-3-031-56060-6_24

- Huang, X., Lian, J., Lei, Y., Yao, J., Lian, D., & Xie, X. (2025). Recommender AI agent: Integrating large language models for interactive recommendations. ACM Transactions on Information Systems, 43(4), Article 96. https://doi.org/10.1145/3731446

- Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W.-t., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. In Advances in Neural Information Processing Systems 33 (NeurIPS 2020) (pp. 9459–9474). Curran Associates. https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html

- Mohbat, F., & Zaki, M. J. (2025). KERL: Knowledge-enhanced personalized recipe recommendation using large language models. In W. Che, J. Nabende, E. Shutova, & M. T. Pilehvar (Eds.), Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) (pp. 19125–19141). Association for Computational Linguistics. https://doi.org/10.18653/v1/2025.acl-long.938

- Salvador, A., Drozdzal, M., Giró-i-Nieto, X., & Romero, A. (2019). Inverse cooking: Recipe generation from food images. In Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR) (pp. 10453–10462). IEEE. https://doi.org/10.1109/CVPR.2019.01070

- Trattner, C., & Elsweiler, D. (2017). Food recommender systems: Important contributions, challenges and future research directions (arXiv:1711.02760). arXiv. https://doi.org/10.48550/arXiv.1711.02760

- Yang, L., Hsieh, C.-K., Yang, H., Pollak, J. P., Dell, N., Belongie, S., Cole, C., & Estrin, D. (2017). Yum-me: A personalized nutrient-based meal recommender system. ACM Transactions on Information Systems, 36(1), Article 7. https://doi.org/10.1145/3072614

- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. In International Conference on Learning Representations (ICLR 2023). https://arxiv.org/abs/2210.03629

- Yin, Y., Qi, H., Zhu, B., Chen, J., Jiang, Y.-G., & Ngo, C.-W. (2025). FoodLMM: A versatile food assistant using large multi-modal model. IEEE Transactions on Multimedia, 27, 6949–6961. https://doi.org/10.1109/TMM.2025.3590924
