# ChefNova — Literature Corpus & Bibliography

This bibliography contains **10 unique papers** reviewed in the team’s four [reflection files](../reflections/), representing **11 paper reviews**. Citations and publication versions follow the reflections. The relevance notes connect the research to ChefNova’s proposed workflow: **grocery receipt → reviewed inventory → quantity confirmation → recipe recommendation**.

## Corpus at a Glance

| # | Paper | Year | Venue | Reviewer(s) |
|---|---|---|---|---|
| 1 | ReAct: Synergizing Reasoning and Acting in Language Models | 2023 | ICLR | Aditya Dilip |
| 2 | Recommender AI Agent (InteRecAgent) | 2025 | ACM TOIS | Aditya Dilip |
| 3 | KERL: Knowledge-Enhanced Personalized Recipe Recommendation Using Large Language Models | 2025 | ACL | Chaitanya Nirantar |
| 4 | Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | 2020 | NeurIPS | Ananya Jandhyala |
| 5 | Large Language Models are Zero-Shot Rankers for Recommender Systems | 2024 | ECIR | Ananya Jandhyala |
| 6 | Personalized Food Recommendation as Constrained Question Answering over a Large-Scale Food Knowledge Graph (pFoodReQ) | 2021 | ACM WSDM | Ananya Jandhyala; Chaitanya Nirantar |
| 7 | Inverse Cooking: Recipe Generation from Food Images | 2019 | CVPR | Prathamesh Mulay |
| 8 | FoodLMM: A Versatile Food Assistant Using Large Multi-Modal Model | 2025 | IEEE TMM | Prathamesh Mulay |
| 9 | Yum-me: A Personalized Nutrient-Based Meal Recommender System | 2017 | ACM TOIS | Prathamesh Mulay |
| 10 | Food Recommender Systems: Important Contributions, Challenges and Future Research Directions | 2017 | arXiv | Aditya Dilip |

## Reflection Coverage

| Team member | Reflection | Papers | Review count |
|---|---|---|---|
| Aditya Dilip | [dilip_aditya.md](../reflections/dilip_aditya.md) | ReAct (#1), InteRecAgent (#2), Food Recommender Systems survey (#10) | 3 |
| Ananya Jandhyala | [Jandhyala_Ananya.md](../reflections/Jandhyala_Ananya.md) | RAG (#4), LLMs as Zero-Shot Rankers (#5), pFoodReQ (#6) | 3 |
| Chaitanya Nirantar | [Nirantar_Chaitanya.md](../reflections/Nirantar_Chaitanya.md) | KERL (#3), pFoodReQ (#6) | 2 |
| Prathamesh Mulay | [Mulay_Prathamesh.md](../reflections/Mulay_Prathamesh.md) | Inverse Cooking (#7), FoodLMM (#8), Yum-me (#9) | 3 |

## Theme A: LLM Agents & Tool Use

*How the orchestrator coordinates tools, user profiles, and recommendation candidates.*

### 1. ReAct
Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. In *International Conference on Learning Representations (ICLR 2023)*. https://arxiv.org/abs/2210.03629

- **Links:** [arXiv](https://arxiv.org/abs/2210.03629) · [Project & code](https://react-lm.github.io)
- **Relevance:** Pattern for our orchestrator, which interleaves reasoning with tool calls (profile, pantry, retrieval, safety) so answers stay grounded in data.

### 2. InteRecAgent
Huang, X., Lian, J., Lei, Y., Yao, J., Lian, D., & Xie, X. (2025). Recommender AI agent: Integrating large language models for interactive recommendations. *ACM Transactions on Information Systems, 43*(4), Article 96. https://doi.org/10.1145/3731446

- **Links:** [DOI](https://doi.org/10.1145/3731446) · [arXiv preprint](https://arxiv.org/abs/2308.16505)
- **Relevance:** Blueprint for "LLM as brain, recommender models as tools," including hard- vs. soft-condition retrieval, a shared candidate bus, like/dislike/expect user profiles, and reflection.

## Theme B: Retrieval, Ranking & Constraint-Aware Recommendation

*How candidates are found, filtered by hard constraints, and ranked.*

### 3. KERL: Knowledge-Enhanced Personalized Recipe Recommendation

Mohbat, F., & Zaki, M. J. (2025). KERL: Knowledge-enhanced personalized recipe recommendation using large language models. In W. Che, J. Nabende, E. Shutova, & M. T. Pilehvar (Eds.), *Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)* (pp. 19125–19141). Association for Computational Linguistics. https://doi.org/10.18653/v1/2025.acl-long.938

- **Links:** [DOI and proceedings](https://doi.org/10.18653/v1/2025.acl-long.938)
- **Relevance:** Motivates a constraint-first pipeline that retrieves food knowledge, validates candidate recipes against explicit requirements, and uses the LLM to adapt and explain recommendations.

### 4. Retrieval-Augmented Generation (RAG)
Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W.-t., Rocktäschel, T., Riedel, S., & Kiela, D. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. In *Advances in Neural Information Processing Systems 33 (NeurIPS 2020)* (pp. 9459–9474). Curran Associates. https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html

- **Links:** [NeurIPS proceedings](https://proceedings.neurips.cc/paper/2020/hash/6b493230205f780e1bc26945df7481e5-Abstract.html) · [arXiv preprint](https://arxiv.org/abs/2005.11401)
- **Relevance:** Foundation for grounding generation in retrieved documents; motivates our "numbers come from data" rule and a swappable recipe index.

### 5. LLMs as Zero-Shot Rankers
Hou, Y., Zhang, J., Lin, Z., Lu, H., Xie, R., McAuley, J., & Zhao, W. X. (2024). Large language models are zero-shot rankers for recommender systems. In *Advances in Information Retrieval: 46th European Conference on Information Retrieval (ECIR 2024)*, Lecture Notes in Computer Science (Vol. 14609, pp. 364–381). Springer. https://doi.org/10.1007/978-3-031-56060-6_24

- **Links:** [DOI](https://doi.org/10.1007/978-3-031-56060-6_24) · [arXiv preprint](https://arxiv.org/abs/2305.08845) · [Code](https://github.com/RUCAIBox/LLMRank)
- **Relevance:** Shows that LLM rerankers suffer from position and popularity bias, and that bootstrapping (shuffling candidates) helps. This directly shapes our ranker design and stability tests.

### 6. pFoodReQ: Personalized Food Recommendation as Constrained QA
Chen, Y., Subburathinam, A., Chen, C.-H., & Zaki, M. J. (2021). Personalized food recommendation as constrained question answering over a large-scale food knowledge graph. In *Proceedings of the 14th ACM International Conference on Web Search and Data Mining (WSDM '21)* (pp. 544–552). Association for Computing Machinery. https://doi.org/10.1145/3437963.3441816

- **Links:** [DOI](https://doi.org/10.1145/3437963.3441816) · [arXiv preprint](https://arxiv.org/abs/2101.01775) · [Code & data](https://github.com/hugochan/PFoodReq)
- **Relevance:** Treats dietary preferences, allergies, and health guidelines as explicit constraints, including negations and numeric bounds. This is the model for our constraint compiler and safety gate.

---

## Theme C: Food Vision & Preference Elicitation

*Lessons from food-image models and preference elicitation for structured receipt extraction and conversational preferences. These papers do not establish receipt-extraction accuracy; ChefNova must evaluate that separately.*

### 7. Inverse Cooking
Salvador, A., Drozdzal, M., Giró-i-Nieto, X., & Romero, A. (2019). Inverse cooking: Recipe generation from food images. In *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)* (pp. 10453–10462). IEEE. https://doi.org/10.1109/CVPR.2019.01070

- **Links:** [DOI](https://doi.org/10.1109/CVPR.2019.01070) · [CVF open access](https://openaccess.thecvf.com/content_CVPR_2019/html/Salvador_Inverse_Cooking_Recipe_Generation_From_Food_Images_CVPR_2019_paper.html) · [arXiv preprint](https://arxiv.org/abs/1812.06164) · [Code](https://github.com/facebookresearch/inversecooking)
- **Relevance:** Separates ingredient extraction from recipe generation. This inspires structured grocery records from receipts, with item names, quantities, and units reviewed by the user before saving.

### 8. FoodLMM
Yin, Y., Qi, H., Zhu, B., Chen, J., Jiang, Y.-G., & Ngo, C.-W. (2025). FoodLMM: A versatile food assistant using large multi-modal model. *IEEE Transactions on Multimedia, 27*, 6949–6961. https://doi.org/10.1109/TMM.2025.3590924

- **Links:** [DOI](https://doi.org/10.1109/TMM.2025.3590924) · [arXiv preprint](https://arxiv.org/abs/2312.14991) · [Code](https://github.com/YuehaoYin/FoodLMM)
- **Relevance:** Highlights structured outputs and domain-specific evaluation. ChefNova applies these lessons to receipt extraction, quantity/unit validation, and user correction; food-image benchmarks do not directly validate grocery-receipt performance.

### 9. Yum-me
Yang, L., Hsieh, C.-K., Yang, H., Pollak, J. P., Dell, N., Belongie, S., Cole, C., & Estrin, D. (2017). Yum-me: A personalized nutrient-based meal recommender system. *ACM Transactions on Information Systems, 36*(1), Article 7. https://doi.org/10.1145/3072614

- **Links:** [DOI](https://doi.org/10.1145/3072614) · [Free full text (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6242282/) · [arXiv preprint](https://arxiv.org/abs/1605.07722) · [Code](https://github.com/ylongqi/yumme)
- **Relevance:** Shows how preference elicitation can reduce user effort while respecting nutritional goals. ChefNova adapts this lesson through conversational preference capture and recommendations grounded in the current, user-confirmed inventory.

---

## Theme D: Food Recommendation, Nutrition & Safety

*How context, taste, nutrition goals, explanations, and real-user evaluation shape food recommendation.*

### 10. Food Recommender Systems Survey
Trattner, C., & Elsweiler, D. (2017). *Food recommender systems: Important contributions, challenges and future research directions* (arXiv:1711.02760). arXiv. https://doi.org/10.48550/arXiv.1711.02760

- **Links:** [arXiv](https://arxiv.org/abs/1711.02760)
- **Relevance:** Maps the field's open problems (context, health-vs-taste trade-offs, weak explanations, and offline-only evaluation) that ChefNova is designed to address.

## Repository Files and Citation Maintenance

The reviewed corpus has two PDFs currently present in this directory: [LLMs as Zero-Shot Rankers](hou2024_llm_zero_shot_rankers.pdf) and [FoodLMM](yin2025_foodlmm.pdf). Other reviewed papers are linked through their DOI, proceedings, or open preprint above. The existing ChatDiet PDF is not counted in this corpus because no current reflection reviews that paper.

This bibliography is synchronized with the four reflection files listed above. The separate [references.bib](references.bib) was not synchronized in this update and should be checked before using it to generate references.

When adding a paper:

1. Add its full citation and review to the appropriate reflection file.
2. Add one bibliography entry and update the reviewer table; list multiple reviewers for a shared paper without counting it twice.
3. Keep the citation metadata and BibTeX entry consistent.
4. Include a PDF only when the license for that exact version permits redistribution; otherwise link to the publisher or an authorized open version.
