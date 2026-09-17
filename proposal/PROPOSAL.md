# ChefNova: Project Proposal

**A conversational cooking assistant grounded in receipt-derived, user-confirmed grocery inventory**

**Team:** Chaitanya Nirantar · [Person 2 — name TBD] · Aditya Dilip · Prathamesh Mulay
**Checkpoint 1 · Fall 2026 · Length: 799 words (Sections 1–5, excluding references)**

---

## 1. Problem Significance

Choosing a meal is a feasibility problem, not a search problem. A student with rice, chickpeas, and spinach who wants a vegetarian dinner in 20 minutes can find recipes easily; the work is deciding what is missing and which substitutions are reasonable. Receipts record what was purchased, not what remains after cooking, so purchase history alone is a poor model of a pantry.

Our hypothesis is that an assistant grounded in user-confirmed ingredients and stated constraints reduces the effort of choosing a meal. We do not claim reductions in food waste, spending, or preparation time; those would require evaluation we have not run.

An AI-native solution is needed because both inputs are unstructured. Receipts use store-specific abbreviations and inconsistent units, and requests arrive as informal sentences carrying several constraints at once, revised in follow-up messages. Fixed parsers and filter forms handle neither, while an unconstrained chatbot cannot be trusted with quantities or dietary rules.

## 2. Prior Work & Gaps

Food recommender research has emphasized offline accuracy, with superficial explanations and few live-system studies (Trattner & Elsweiler, 2017). pFoodReQ treats dietary preferences and health guidelines as explicit constraints over a food knowledge graph, handling negations and numeric comparisons, but answers templated questions and assumes no pantry (Chen et al., 2021). InteRecAgent pairs an LLM planner with recommender tools and keeps a user profile across turns (X. Huang et al., 2025); ReAct grounds model reasoning in tool calls (Yao et al., 2023). Two findings shape our caution: ChatDiet reports explanations that contradicted its own evidence (Yang et al., 2024), and LLM rankers are biased by candidate position and popularity (Hou et al., 2024).

Receipt parsing has a separate literature: LayoutLMv3 pre-trains on text and images for receipt and form understanding (Y. Huang et al., 2022), and Donut parses documents without an OCR stage (Kim et al., 2022). Neither line connects receipt-derived, user-confirmed quantities to constraint-preserving recommendation — the gap ChefNova explores.

## 3. Proposed Technical Approach

The interaction has six steps: upload a receipt, review the extracted groceries, save quantities, request a recipe, confirm or edit the inventory, and receive recommendations. The prototype accepts PNG/JPG receipts, sends images to Gemini for extraction, and stores results in local SQLite, deduplicated per user by receipt bytes; matching names and units are added together, and differing units stay separate.

Four modules carry the work: extraction turns a receipt image into item, quantity, and unit fields in an editable table; the inventory store persists confirmed quantities; a request interpreter converts informal requests into structured constraints that survive later turns; and recommendation combines retrieved recipe data with the confirmed inventory, with a feasibility check in code comparing required amounts to stored quantities.

Generation handles extraction, interpretation, and explanation; persistence and arithmetic are database operations; the user resolves uncertain extractions. Person 3 will specify which operations require generation, which use retrieved recipe data, and which need validation.

## 4. Checkpoint 2 Validation Plan

We will validate the chains carrying the most risk, using a fixed request set and logging every run.

- **Receipt extraction:** field-level accuracy for item, quantity, and unit across receipts of varied quality, with edits per receipt measuring correction effort.
- **Constraint preservation:** multi-turn conversations that add and revise constraints, scored by constraint violation rate.
- **Ingredient reasoning:** required, optional, and substitutable cases, plus conflicts where a core ingredient is missing.
- **Process invariant:** no recommendation is produced before inventory confirmation.
- **Quantity feasibility:** recommended amounts compared against stored quantities.

Two annotators will label a shared subset to report agreement. Person 3 will define the test cases and acceptance thresholds. Results will be reported as pass or fail per case with error analysis, not a single headline score.

## 5. Risk Analysis & Mitigation

**Privacy and data security.** Receipts reveal purchase history, timestamps, store location, and sometimes partial card numbers. Images are sent to Gemini and not persisted locally; we will document that processing, keep only extracted fields, and use no real receipts in demos. Local profile names are not authentication and will not be described as access control.

**Bias and toxicity.** Recipe sources and model priors skew toward particular cuisines, and LLM ranking favors popular items (Hou et al., 2024). We will check cuisine variety and avoid moralizing language about food or body weight.

**Safety.** Dietary filtering in the prototype is not verified allergy safety: one study found ChatGPT diets that still contained an allergen, such as almond milk in a nut-free diet (Niszczota & Rybicka, 2023). The interface will state that suggestions are not allergy-safe and flag ambiguous ingredients rather than clearing them.

**Hallucination.** Quantities are compared in code, not generated. Nutrition values will not be presented as measured facts, missing ingredients will be listed, and the assistant should say when information is insufficient rather than invent a substitution.

---

## References

*These must match the entries in `literature/BIBLIOGRAPHY.md`.*

- Chen, Y., Subburathinam, A., Chen, C.-H., & Zaki, M. J. (2021). Personalized food recommendation as constrained question answering over a large-scale food knowledge graph. In *Proceedings of the 14th ACM International Conference on Web Search and Data Mining (WSDM '21)* (pp. 544–552). Association for Computing Machinery. https://doi.org/10.1145/3437963.3441816
- Hou, Y., Zhang, J., Lin, Z., Lu, H., Xie, R., McAuley, J., & Zhao, W. X. (2024). Large language models are zero-shot rankers for recommender systems. In *Advances in Information Retrieval (ECIR 2024)*, Lecture Notes in Computer Science (Vol. 14609, pp. 364–381). Springer. https://doi.org/10.1007/978-3-031-56060-6_24
- Huang, X., Lian, J., Lei, Y., Yao, J., Lian, D., & Xie, X. (2025). Recommender AI agent: Integrating large language models for interactive recommendations. *ACM Transactions on Information Systems, 43*(4), Article 96. https://doi.org/10.1145/3731446
- Huang, Y., Lv, T., Cui, L., Lu, Y., & Wei, F. (2022). LayoutLMv3: Pre-training for document AI with unified text and image masking. In *Proceedings of the 30th ACM International Conference on Multimedia (MM '22)*. Association for Computing Machinery. https://arxiv.org/abs/2204.08387
- Kim, G., Hong, T., Yim, M., Nam, J., Park, J., Yim, J., Hwang, W., Yun, S., Han, D., & Park, S. (2022). OCR-free document understanding transformer. In *Computer Vision – ECCV 2022*. Springer. https://arxiv.org/abs/2111.15664
- Niszczota, P., & Rybicka, I. (2023). The credibility of dietary advice formulated by ChatGPT: Robo-diets for people with food allergies. *Nutrition, 112*, Article 112076. https://doi.org/10.1016/j.nut.2023.112076
- Trattner, C., & Elsweiler, D. (2017). *Food recommender systems: Important contributions, challenges and future research directions* (arXiv:1711.02760). arXiv. https://doi.org/10.48550/arXiv.1711.02760
- Yang, Z., Khatibi, E., Nagesh, N., Abbasian, M., Azimi, I., Jain, R., & Rahmani, A. M. (2024). ChatDiet: Empowering personalized nutrition-oriented food recommender chatbots through an LLM-augmented framework. *Smart Health, 32*, Article 100465. https://doi.org/10.1016/j.smhl.2024.100465
- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. In *International Conference on Learning Representations (ICLR 2023)*. https://arxiv.org/abs/2210.03629
