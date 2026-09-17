Individual Reflection: Nirantar Chaitanya





Role

Personalized Recommendation & Constraint-Aware Recipe Intelligence

Project

ChefNova: An Agentic AI Personal Chef

Papers reviewed

(1) KERL, Mohbat & Zaki (2025) · (2) Personalized Food Recommendation, Chen et al. (2021)

Last updated

September 2026

Paper 1: KERL — Knowledge-Enhanced Personalized Recipe Recommendation Using Large Language Models

Full Citation & Link

Mohbat, F., & Zaki, M. J. (2025). KERL: Knowledge-enhanced personalized recipe recommendation using large language models. In W. Che, J. Nabende, E. Shutova, & M. T. Pilehvar (Eds.), Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) (pp. 19125–19141). Association for Computational Linguistics. https://doi.org/10.18653/v1/2025.acl-long.938

Structured Summary

KERL addresses the gap between general-purpose LLM recipe generation and personalized food recommendations that must satisfy explicit user constraints. The system extracts entities from a natural-language request, queries FoodKG for a relevant subgraph, and passes the retrieved knowledge to an LLM as grounded context. It separates recommendation, recipe-instruction generation, and nutritional-information generation into specialized modules using task-specific LoRA adapters. The authors also construct benchmark data combining recipe questions with constraints and personal preferences, then evaluate recommendation quality as well as generated recipes and nutrition estimates. The experiments show that knowledge-grounded generation can outperform prior approaches, supporting an architecture in which ChefNova retrieves and validates food knowledge before presenting a recipe.

Three Key Insights

Retrieve before generating. A food knowledge graph gives the LLM explicit ingredients, tags, relationships, and nutrition context instead of relying only on parameters learned during pretraining.

Treat constraints as structured inputs. Dietary rules and personal preferences can be extracted from the request and checked against retrieved recipe candidates before generation begins.

Use specialized modules for different outputs. Recommendation, cooking instructions, and nutrition estimation have different objectives, so task-specific adapters can be more dependable than one undifferentiated prompt.

Two Limitations / Risks

The system remains dependent on the coverage and correctness of FoodKG; missing or incorrect ingredient relationships can lead to incomplete retrieval and weak recommendations.

KERL does not automatically convert every medical condition into clinically appropriate dietary restrictions, so its output must not be treated as medical advice or as a substitute for expert validation.

Concrete Inspiration for ChefNova

ChefNova should implement a constraint-first RAG pipeline: convert the user's request and saved profile into structured constraints, retrieve candidate recipes and relevant ingredient facts, reject candidates that violate hard restrictions, and only then use the LLM to adapt and explain the best options.

Paper 2: Personalized Food Recommendation as Constrained Question Answering over a Large-Scale Food Knowledge Graph

Full Citation & Link

Chen, Y., Subburathinam, A., Chen, C.-H., & Zaki, M. J. (2021). Personalized food recommendation as constrained question answering over a large-scale food knowledge graph. In Proceedings of the 14th ACM International Conference on Web Search and Data Mining (pp. 544–552). Association for Computing Machinery. https://doi.org/10.1145/3437963.3441816

Structured Summary

This paper frames personalized food recommendation as constrained question answering over a large food knowledge graph rather than as ordinary similarity-based ranking. The proposed pFoodReQ framework expands a user's immediate query with persistent dietary preferences, allergies, health guidelines, and food-history signals. It introduces mechanisms for handling negative requirements and numerical comparisons, which are important for requests such as excluding an allergen or limiting calories. The authors build a benchmark from FoodKG and health guidelines and report substantially better results than non-personalized baselines, including an average absolute improvement of 59.7% across evaluation metrics. The work demonstrates that explicit constraint reasoning is essential when a recommender must balance relevance, personalization, nutrition, and safety.

Three Key Insights

A profile should augment each request. Long-term information such as allergies, diet, nutrition targets, and prior food choices must remain available even when the user does not repeat it in every prompt.

Negative and numeric constraints need explicit logic. “No peanuts” and “under 600 calories” should be evaluated deterministically rather than left to semantic similarity or free-form language generation.

History improves ranking after safety filtering. Previous meals and feedback can personalize the order of valid candidates without weakening non-negotiable restrictions.

Two Limitations / Risks

Much of the benchmark uses template-generated questions and randomly generated preferences, so performance may not transfer directly to messy, ambiguous requests from real households.

The food-history evaluation uses simulated logs rather than long-term behavior from real users, limiting the evidence that the approach can learn changing preferences over time.

Concrete Inspiration for ChefNova

ChefNova should maintain a persistent preference-and-safety profile and compile it with each new request into two layers: hard filters for allergies, exclusions, and numeric nutrition limits, followed by a soft ranker for cuisine preference, pantry use, preparation time, and the user's past likes or dislikes.

Combined Design Takeaway for ChefNova

Together, the papers suggest the following recommendation flow:

User request + saved profile → constraint compiler → knowledge-graph/recipe retrieval → hard safety filter → personalized ranking → LLM explanation and recipe adaptation

This design keeps allergies and dietary restrictions non-negotiable while still allowing ChefNova to learn preferences and provide flexible, conversational recipes. It also makes recommendations more traceable because the system can show which profile rule, ingredient fact, or nutrition constraint affected the result.
