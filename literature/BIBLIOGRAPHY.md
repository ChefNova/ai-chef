# Literature Corpus & Bibliography

This corpus contains **12 papers** that ground RecipeRAG's design. They are grouped into four themes that map onto the system architecture, and each paper is assigned to one team member, who reviews it in [`/reflections/`](../reflections/). Citations follow **APA 7th edition**; BibTeX for every entry is in [`references.bib`](references.bib).

## Corpus at a Glance

| # | Paper | Year | Venue | Theme | Reviewer | PDF in repo |
|---|---|---|---|---|---|---|
| 1 | ReAct: Synergizing Reasoning and Acting in Language Models | 2023 | ICLR | A. Agents & memory | Aditya Dilip | [Yes](yao2023_react.pdf) (CC BY 4.0) |
| 2 | Recommender AI Agent (InteRecAgent) | 2025 | ACM TOIS | A. Agents & memory | Aditya Dilip | Link only |
| 3 | Generative Agents: Interactive Simulacra of Human Behavior | 2023 | ACM UIST | A. Agents & memory | {{MEMBER4_NAME}} | Link only |
| 4 | Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks | 2020 | NeurIPS | B. Retrieval & ranking | {{MEMBER2_NAME}} | Link only |
| 5 | Large Language Models are Zero-Shot Rankers for Recommender Systems | 2024 | ECIR | B. Retrieval & ranking | {{MEMBER2_NAME}} | [Yes](hou2024_llm_zero_shot_rankers.pdf) (CC BY 4.0) |
| 6 | Personalized Food Recommendation as Constrained QA over a Food KG | 2021 | ACM WSDM | B. Retrieval & ranking | {{MEMBER2_NAME}} | Link only |
| 7 | Inverse Cooking: Recipe Generation from Food Images | 2019 | CVPR | C. Food vision & preference | {{MEMBER3_NAME}} | Link only |
| 8 | FoodLMM: A Versatile Food Assistant Using Large Multi-Modal Model | 2025 | IEEE TMM | C. Food vision & preference | {{MEMBER3_NAME}} | [Yes](yin2025_foodlmm.pdf) (CC BY-NC-ND 4.0) |
| 9 | Yum-me: A Personalized Nutrient-Based Meal Recommender System | 2017 | ACM TOIS | C. Food vision & preference | {{MEMBER3_NAME}} | Link only |
| 10 | Food Recommender Systems: Important Contributions, Challenges and Future Research Directions | 2017 | arXiv | D. Food recsys, nutrition & safety | Aditya Dilip | Link only |
| 11 | ChatDiet: Personalized Nutrition-Oriented Food Recommender Chatbots | 2024 | Smart Health | D. Food recsys, nutrition & safety | {{MEMBER4_NAME}} | [Yes](yang2024_chatdiet.pdf) (CC BY 4.0) |
| 12 | The Credibility of Dietary Advice Formulated by ChatGPT: Robo-Diets for People with Food Allergies | 2023 | Nutrition | D. Food recsys, nutrition & safety | {{MEMBER4_NAME}} | Link only |

**Reviewer load:** Aditya Dilip (#1, #2, #10) · {{MEMBER2_NAME}} (#4, #5, #6) · {{MEMBER3_NAME}} (#7, #8, #9) · {{MEMBER4_NAME}} (#3, #11, #12)

---

## Theme A: LLM Agents, Tool Use & Memory

*How the orchestrator plans, calls tools, and remembers users.*

### 1. ReAct
Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. In *International Conference on Learning Representations (ICLR 2023)*. https://arxiv.org/abs/2210.03629

- **Links:** [arXiv](https://arxiv.org/abs/2210.03629) · [Project & code](https://react-lm.github.io)
- **Relevance:** Pattern for our orchestrator, which interleaves reasoning with tool calls (profile, pantry, retrieval, safety) so answers stay grounded in data.

### 2. InteRecAgent
Huang, X., Lian, J., Lei, Y., Yao, J., Lian, D., & Xie, X. (2025). Recommender AI agent: Integrating large language models for interactive recommendations. *ACM Transactions on Information Systems, 43*(4), Article 96. https://doi.org/10.1145/3731446

- **Links:** [DOI](https://doi.org/10.1145/3731446) · [arXiv preprint](https://arxiv.org/abs/2308.16505)
- **Relevance:** Blueprint for "LLM as brain, recommender models as tools," including hard- vs. soft-condition retrieval, a shared candidate bus, like/dislike/expect user profiles, and reflection.

### 3. Generative Agents
Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. In *Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology (UIST '23)* (pp. 1–22). Association for Computing Machinery. https://doi.org/10.1145/3586183.3606763

- **Links:** [DOI](https://doi.org/10.1145/3586183.3606763) · [arXiv preprint](https://arxiv.org/abs/2304.03442)
- **Relevance:** Memory architecture (retrieval by recency, importance, and relevance, plus periodic reflection) that we adapt for long-term taste memory.

---

## Theme B: Retrieval, Ranking & Constraint-Aware Recommendation

*How candidates are found, filtered by hard constraints, and ranked.*

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

*How photos become ingredients, and how taste is learned quickly.*

### 7. Inverse Cooking
Salvador, A., Drozdzal, M., Giró-i-Nieto, X., & Romero, A. (2019). Inverse cooking: Recipe generation from food images. In *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)* (pp. 10453–10462). IEEE. https://doi.org/10.1109/CVPR.2019.01070

- **Links:** [DOI](https://doi.org/10.1109/CVPR.2019.01070) · [CVF open access](https://openaccess.thecvf.com/content_CVPR_2019/html/Salvador_Inverse_Cooking_Recipe_Generation_From_Food_Images_CVPR_2019_paper.html) · [arXiv preprint](https://arxiv.org/abs/1812.06164) · [Code](https://github.com/facebookresearch/inversecooking)
- **Relevance:** Treats ingredients as an unordered *set* predicted from an image. We use the same representation and set-based metrics for pantry detection.

### 8. FoodLMM
Yin, Y., Qi, H., Zhu, B., Chen, J., Jiang, Y.-G., & Ngo, C.-W. (2025). FoodLMM: A versatile food assistant using large multi-modal model. *IEEE Transactions on Multimedia, 27*, 6949–6961. https://doi.org/10.1109/TMM.2025.3590924

- **Links:** [DOI](https://doi.org/10.1109/TMM.2025.3590924) · [arXiv preprint](https://arxiv.org/abs/2312.14991) · [Code](https://github.com/YuehaoYin/FoodLMM)
- **Relevance:** State of the art in food-specialized multimodal LLMs (ingredient recognition, nutrition estimation, segmentation). It sets expectations for, and the limits of, our photo-to-pantry agent.

### 9. Yum-me
Yang, L., Hsieh, C.-K., Yang, H., Pollak, J. P., Dell, N., Belongie, S., Cole, C., & Estrin, D. (2017). Yum-me: A personalized nutrient-based meal recommender system. *ACM Transactions on Information Systems, 36*(1), Article 7. https://doi.org/10.1145/3072614

- **Links:** [DOI](https://doi.org/10.1145/3072614) · [Free full text (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6242282/) · [arXiv preprint](https://arxiv.org/abs/1605.07722) · [Code](https://github.com/ylongqi/yumme)
- **Relevance:** Visual-quiz preference elicitation plus nutrient-goal filtering. This inspires our 60-second visual taste onboarding and the rule that goals filter while taste ranks.

---

## Theme D: Food Recommendation, Nutrition & Safety

*What the field has learned, where LLM nutrition advice succeeds, and where it fails.*

### 10. Food Recommender Systems Survey
Trattner, C., & Elsweiler, D. (2017). *Food recommender systems: Important contributions, challenges and future research directions* (arXiv:1711.02760). arXiv. https://doi.org/10.48550/arXiv.1711.02760

- **Links:** [arXiv](https://arxiv.org/abs/1711.02760)
- **Relevance:** Maps the field's open problems (context, health-vs-taste trade-offs, weak explanations, and offline-only evaluation) that RecipeRAG is designed to address.

### 11. ChatDiet
Yang, Z., Khatibi, E., Nagesh, N., Abbasian, M., Azimi, I., Jain, R., & Rahmani, A. M. (2024). ChatDiet: Empowering personalized nutrition-oriented food recommender chatbots through an LLM-augmented framework. *Smart Health, 32*, Article 100465. https://doi.org/10.1016/j.smhl.2024.100465

- **Links:** [DOI](https://doi.org/10.1016/j.smhl.2024.100465) · [arXiv preprint](https://arxiv.org/abs/2403.00781)
- **Relevance:** Closest LLM-based prior system (orchestrator plus personal and population models). Its documented hallucinated explanations motivate our claim-level faithfulness check.

### 12. Robo-Diets for People with Food Allergies
Niszczota, P., & Rybicka, I. (2023). The credibility of dietary advice formulated by ChatGPT: Robo-diets for people with food allergies. *Nutrition, 112*, Article 112076. https://doi.org/10.1016/j.nut.2023.112076

- **Links:** [DOI](https://doi.org/10.1016/j.nut.2023.112076) · [PubMed](https://pubmed.ncbi.nlm.nih.gov/37269717/)
- **Relevance:** Evidence that a general chatbot can put hidden allergens in "safe" diets, the core risk our deterministic safety gate and allergen red-team suite address.

---

## PDF Policy

We commit PDFs **only when the license permits redistribution**:

| File | Source version | License |
|---|---|---|
| [`yao2023_react.pdf`](yao2023_react.pdf) | arXiv 2210.03629 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) |
| [`hou2024_llm_zero_shot_rankers.pdf`](hou2024_llm_zero_shot_rankers.pdf) | arXiv 2305.08845 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) |
| [`yang2024_chatdiet.pdf`](yang2024_chatdiet.pdf) | arXiv 2403.00781 | [CC BY 4.0](http://creativecommons.org/licenses/by/4.0/) |
| [`yin2025_foodlmm.pdf`](yin2025_foodlmm.pdf) | arXiv 2312.14991v2 | [CC BY-NC-ND 4.0](http://creativecommons.org/licenses/by-nc-nd/4.0/) (unmodified, non-commercial) |

All other papers are distributed under arXiv's non-exclusive license or publisher copyright, which does not grant third-party redistribution. For those, we link to the DOI and to free, legal full-text versions (arXiv, CVF Open Access, PubMed Central) instead.

## Adding a Paper

1. Add the BibTeX entry to [`references.bib`](references.bib) (key format: `firstauthorYEARkeyword`).
2. Add the APA citation, links, and a one-line relevance note under the right theme above, and add a row to the table.
3. Commit the PDF only if its license permits redistribution, and record the license in the PDF policy table.
4. Open a PR that references the corresponding issue.
