# ChefNova: Project Proposal

**An agentic AI personal chef that recommends real, allergy-safe recipes from your pantry, preferences, and nutrition goals**

**Team:** Aditya Dilip (Lead), {{MEMBER2_NAME}}, {{MEMBER3_NAME}}, {{MEMBER4_NAME}} · **Checkpoint 1** · Fall 2026 · **Length:** 740 words (Sections 1–5, excluding references)

---

## 1. Problem Significance

Deciding what to cook is a daily constraint-satisfaction problem. A good meal must use what is on hand, respect dietary rules and nutrition goals, suit the cook's taste, and, for many people, contain no allergens. The stakes are real: 10.8% of U.S. adults have a convincing food allergy, and over half of them have had a severe reaction (Gupta et al., 2019). Households also generate 60% of global food waste (UNEP, 2024). Today, people juggle these constraints by hand across recipe sites, pantry apps, and nutrition trackers.

This problem needs an AI-native solution because its inputs are unstructured: a cluttered fridge photo, a request like "no cilantro, mild, about 40 g protein," and a history of meals that were loved or skipped. Rule-based filters can't interpret these inputs, and an unconstrained chatbot can't be trusted with them. When ChatGPT designed diets for people with food allergies, it was generally accurate but produced harmful errors, such as almond milk in a nut-free diet (Niszczota & Rybicka, 2023). RecipeRAG combines LLM flexibility with grounded data and enforceable rules.

## 2. Prior Work & Gaps

Food recommender research has emphasized offline accuracy, with superficial explanations and few real-user studies (Trattner & Elsweiler, 2017). Yum-me learns taste through a visual quiz and filters by nutrient goals, but it uses a static recipe pool and ignores the pantry (Yang et al., 2017). pFoodReQ models allergies and health guidelines as constraints over a food knowledge graph, but it answers templated questions, not conversations or photos (Chen et al., 2021). ChatDiet adds an LLM orchestrator for explainable nutrition advice, yet it depends on one person's wearable data and documents explanations that contradict its own causal model (Yang et al., 2024).

Agent research supplies building blocks but not this safety-critical integration. ReAct grounds reasoning in tool use (Yao et al., 2023), InteRecAgent pairs an LLM planner with recommender tools (Huang et al., 2025), generative agents retrieve memories by recency, importance, and relevance (Park et al., 2023), and RAG grounds generation in retrieved documents (Lewis et al., 2020). However, LLM rankers show position and popularity bias (Hou et al., 2024), and food vision models target plated dishes rather than cluttered fridges (Salvador et al., 2019; Yin et al., 2025). **No existing system unifies pantry perception, grounded retrieval, deterministic safety, and long-term taste memory.**

## 3. Proposed Technical Approach

**Interaction flow.** (1) Onboarding captures diet, allergies with severity, dislikes, goals, and an optional visual taste quiz. (2) The user photographs the fridge and confirms the detected ingredients. (3) The user makes a request and receives five ranked recipes, each with a grounded explanation and a source link. (4) Feedback (cooked, loved, skipped) updates memory.

**GenAI and agentic modules.**

- **Orchestrator:** a tool-calling LLM running a bounded ReAct loop with a critic step.
- **Pantry vision agent:** a multimodal LLM that returns schema-validated ingredient JSON with confidence scores.
- **Profile and memory agent:** pinned facts (allergies, diet) plus decaying taste memories.
- **Retrieval tools:** Spoonacular with hard filters, and a RecipeNLG embedding index for vague requests.
- **Safety gate:** deterministic code that checks every ingredient against an allergen-derivative lexicon.
- **Ranker:** scores pantry coverage, goal fit, taste, and diversity, then applies shuffle-bootstrapped LLM reranking.
- **Explainer:** verifies every claim against retrieved data; numbers are copied, never generated.

## 4. Checkpoint 2 Validation Plan

We will test each chain in isolation, then end to end, using a pytest harness that runs in continuous integration.

| Component | Test set | Metric and target |
|---|---|---|
| Preference parsing | 60 synthetic personas | Slot F1 ≥ 0.90 |
| Pantry vision | 40+ labeled fridge photos | Set F1 ≥ 0.80 on visible items |
| Safety gate | 200+ adversarial allergen cases | Zero post-gate violations |
| Ranking | 50 persona–request pairs | nDCG@5 vs. baselines; judge calibrated on human labels; stability across shuffles |
| Grounding | All explanations | ≥ 95% of claims supported |
| Reliability | Full suite | Tool-call success, p95 latency, API cost |

## 5. Risk Analysis & Mitigation

| Risk | Mitigation |
|---|---|
| **Privacy and data security:** allergies, goals, and photos are sensitive | Minimize data collected; delete photos after extraction; encrypt profiles; keep API keys server-side; let users edit or delete memory |
| **Bias and toxicity:** Western-centric corpora, popularity bias, diet-culture language | Audit cuisine diversity; add diversity to ranking; follow a tone guide that bans moralizing food language; flag extreme calorie goals |
| **Safety:** hidden allergens | Enforce a deterministic gate with a derivative lexicon; flag ambiguous ingredients; offer a strict mode; show a check-labels notice |
| **Hallucination:** invented recipes or numbers, misread photos | Retrieve recipes only; validate candidate IDs; require user-confirmed pantry; verify claims; return "no safe match found" instead of guessing |

---

## References

*Corpus papers are listed in full, with links, in [`/literature/BIBLIOGRAPHY.md`](../literature/BIBLIOGRAPHY.md).*

- Chen, Y., Subburathinam, A., Chen, C.-H., & Zaki, M. J. (2021). Personalized food recommendation as constrained question answering over a large-scale food knowledge graph. In *Proceedings of WSDM '21* (pp. 544–552). ACM. https://doi.org/10.1145/3437963.3441816
- Gupta, R. S., Warren, C. M., Smith, B. M., Jiang, J., Blumenstock, J. A., Davis, M. M., Schleimer, R. P., & Nadeau, K. C. (2019). Prevalence and severity of food allergies among US adults. *JAMA Network Open, 2*(1), e185630. https://doi.org/10.1001/jamanetworkopen.2018.5630
- Hou, Y., Zhang, J., Lin, Z., Lu, H., Xie, R., McAuley, J., & Zhao, W. X. (2024). Large language models are zero-shot rankers for recommender systems. In *ECIR 2024*, LNCS 14609 (pp. 364–381). Springer. https://doi.org/10.1007/978-3-031-56060-6_24
- Huang, X., Lian, J., Lei, Y., Yao, J., Lian, D., & Xie, X. (2025). Recommender AI agent: Integrating large language models for interactive recommendations. *ACM Transactions on Information Systems, 43*(4), Article 96. https://doi.org/10.1145/3731446
- Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W.-t., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. In *Advances in Neural Information Processing Systems 33* (pp. 9459–9474). https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html
- Niszczota, P., & Rybicka, I. (2023). The credibility of dietary advice formulated by ChatGPT: Robo-diets for people with food allergies. *Nutrition, 112*, Article 112076. https://doi.org/10.1016/j.nut.2023.112076
- Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. In *Proceedings of UIST '23* (pp. 1–22). ACM. https://doi.org/10.1145/3586183.3606763
- Salvador, A., Drozdzal, M., Giró-i-Nieto, X., & Romero, A. (2019). Inverse cooking: Recipe generation from food images. In *Proceedings of CVPR 2019* (pp. 10453–10462). IEEE. https://doi.org/10.1109/CVPR.2019.01070
- Trattner, C., & Elsweiler, D. (2017). *Food recommender systems: Important contributions, challenges and future research directions* (arXiv:1711.02760). arXiv. https://doi.org/10.48550/arXiv.1711.02760
- United Nations Environment Programme. (2024). *Food Waste Index Report 2024*. https://www.unep.org/resources/publication/food-waste-index-report-2024
- Yang, L., Hsieh, C.-K., Yang, H., Pollak, J. P., Dell, N., Belongie, S., Cole, C., & Estrin, D. (2017). Yum-me: A personalized nutrient-based meal recommender system. *ACM Transactions on Information Systems, 36*(1), Article 7. https://doi.org/10.1145/3072614
- Yang, Z., Khatibi, E., Nagesh, N., Abbasian, M., Azimi, I., Jain, R., & Rahmani, A. M. (2024). ChatDiet: Empowering personalized nutrition-oriented food recommender chatbots through an LLM-augmented framework. *Smart Health, 32*, Article 100465. https://doi.org/10.1016/j.smhl.2024.100465
- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. In *ICLR 2023*. https://arxiv.org/abs/2210.03629
- Yin, Y., Qi, H., Zhu, B., Chen, J., Jiang, Y.-G., & Ngo, C.-W. (2025). FoodLMM: A versatile food assistant using large multi-modal model. *IEEE Transactions on Multimedia, 27*, 6949–6961. https://doi.org/10.1109/TMM.2025.3590924
