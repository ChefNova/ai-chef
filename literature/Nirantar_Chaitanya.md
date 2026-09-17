# ChefNova Literature Reflection — Nirantar Chaitanya

## Papers Selected


**Mohbat, F., & Zaki, M. J. (2025). “KERL: Knowledge-Enhanced Personalized Recipe Recommendation using Large Language Models.”** This is a peer-reviewed ACL 2025 long paper, published in the *Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics*, pages 19125–19141. KERL combines FoodKG retrieval with an LLM and separate LoRA adapters for personalized recommendation, recipe generation, and nutritional information. citeturn10view0turn7view0

**Chen, Y., Subburathinam, A., Chen, C.-H., & Zaki, M. J. (2021). “Personalized Food Recommendation as Constrained Question Answering over a Large-scale Food Knowledge Graph.”** This WSDM 2021 paper formulates personalized food recommendation as constrained question answering over FoodKG, incorporating dietary preferences, allergies, health guidelines, and food-history signals. citeturn4view1turn8search13

## What the Reflection Emphasizes

For **KERL**, the reflection focuses on the idea that ChefNova should **retrieve and constrain before it generates**. KERL retrieves relevant FoodKG subgraphs from a natural-language request and supplies them as grounded context to the LLM; it then separates recommendation, cooking-instruction generation, and nutrition generation into specialized modules. Its recommendation component achieved an F1 of **0.854 on the pFoodReq benchmark versus 0.637 for pFoodReq**, while the authors explicitly caution that recommendations remain dependent on KG coverage and that the system does not automatically translate medical conditions such as diabetes into the correct dietary restrictions. citeturn5view0turn6view0

For the **Chen et al. paper**, the reflection emphasizes persistent user memory and explicit constraint handling. Its architecture expands the immediate query with profile information, handles numerical nutrition requirements through KG augmentation, explicitly models negative constraints, and can incorporate food-history similarity during ranking. Particularly relevant to ChefNova, removing query expansion caused a very large performance drop, while removing constraint modeling reduced F1 from **63.7 to 25.9**, showing why an allergy or “do not include” rule should not simply be left to embedding similarity or an LLM prompt. citeturn6view1turn6view2

The reflection also critically examines the papers instead of only summarizing them. For example, the Chen et al. benchmark uses template-generated questions and randomly generated preferences, while its food-history experiments rely on **30 simulated food logs across five diet styles** rather than longitudinal data from real users. citeturn13view0turn13view2

The final project inspiration combines the strongest ideas from both papers into a ChefNova architecture:

**User/Profile → Constraint Compiler → Recipe Retrieval → Hard Safety Filter → Personalized Ranker → LLM Explanation/Adaptation**

This allows allergies and dietary restrictions to function as non-negotiable filters while cuisine preferences, pantry utilization, nutrition goals, cooking time, and previous likes/dislikes influence ranking.

## Research Basis

The file uses the official **ACL Anthology** record for KERL, which confirms its ACL 2025 publication metadata, DOI, venue, and page range. citeturn10view0 The KERL paper describes FoodKG-backed retrieval, SPARQL-based subgraph construction, the multi-LoRA architecture, and the three recommendation/recipe/nutrition modules. citeturn7view0turn5view0

For the second paper, the WSDM publication metadata and methodology were checked against the paper itself and IBM Research's publication record. The study reports that pFoodReQ incorporates user preferences and health guidelines as constraints and substantially outperforms its non-personalized baselines; its human evaluation also places pFoodReQ above the compared systems. citeturn4view1turn6view1turn12search1

**[Download the finished `Nirantar_Chaitanya.md`](sandbox:/mnt/data/Nirantar_Chaitanya.md)**
