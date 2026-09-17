# Individual Reflection: Mulay Prathamesh

| | |
|---|---|
| **Role** | Pantry Vision & Multimodal UX |
| **Project** | RecipeRAG: An Agentic AI Personal Chef |
| **Papers reviewed** | (1) Inverse Cooking, Salvador et al. (2019) · (2) FoodLMM, Yin et al. (2025) · (3) Yum-me, Yang et al. (2017) |
| **Last updated** | September 2026 |

---

## Paper 1: Inverse Cooking: Recipe Generation from Food Images

### 1. Full Citation & Link

Salvador, A., Drozdzal, M., Giró-i-Nieto, X., & Romero, A. (2019). Inverse cooking: Recipe generation from food images. In *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)* (pp. 10453–10462). IEEE. https://doi.org/10.1109/CVPR.2019.01070

**Link:** https://openaccess.thecvf.com/content_CVPR_2019/html/Salvador_Inverse_Cooking_Recipe_Generation_From_Food_Images_CVPR_2019_paper.html · Preprint: https://arxiv.org/abs/1812.06164 · Code: https://github.com/facebookresearch/inversecooking

### 2. Structured Summary

**Research problem.** Food images contain rich information about ingredients and preparation, but earlier image-to-recipe systems mostly *retrieved* existing recipes from a fixed dataset, an approach that fails whenever no matching recipe exists. **Methodology.** Salvador et al. instead generate a complete recipe from a single food image in two stages. First, the model predicts the ingredients as an unordered set, using an architecture that models dependencies among ingredients without imposing an order on them. Second, a transformer generates cooking instructions by attending to both the image and the predicted ingredients; the full system is trained and evaluated on the large-scale Recipe1M dataset. **Main findings.** The approach improved ingredient prediction over previous baselines and produced high-quality recipes. In a human evaluation, its generated recipes were judged more compelling than those returned by retrieval-based approaches.

### 3. Three Key Insights

1. **Ingredients are a set, not a sequence.** Modeling ingredients as an unordered set means a model isn't penalized for listing "garlic, onion" instead of "onion, garlic." Our pantry detector should be evaluated the same way, with set-based precision, recall, and F1 rather than sequence-matching metrics.
2. **Separate perception from what you do with it.** Splitting "what is in the image" from "what to cook" makes each stage easier to improve and evaluate on its own. RecipeRAG keeps the perception stage and replaces free-form generation with retrieval of real, tested recipes.
3. **An ingredient set is a reusable bridge.** Once a photo becomes a clean ingredient set, it can drive recipe retrieval, substitutions, and "what am I missing?" shopping lists. That set, not a dish name or a caption, should be the vision agent's output contract.

### 4. Two Limitations or Risks

1. **Plated dishes are not fridge shelves.** Recipe1M images show finished, plated food, while our photos contain packaged, stacked, occluded, and partly visible items (a jar behind the milk, a vegetable in an opaque bag). Accuracy on plated food won't transfer directly to fridges and pantries, and some ingredients, such as oil in a pan or butter in a sauce, aren't visible in any photo.
2. **Generated recipes are unverified.** Instructions generated from an image can be plausible but untested, with no guarantees about quantities, cooking safety (for example, safe internal temperatures for meat), or allergens. That is acceptable for research but not for a consumer product that tells people what to eat.

### 5. One Concrete Inspiration for RecipeRAG

**Set-based pantry evaluation plus a "hidden staples" profile.** Our vision agent will output an ingredient set with a confidence score per item, evaluated against human-labeled fridge and pantry photos using set precision, recall, and F1. Because many staples are never visible, onboarding will ask once which staples the user keeps on hand (oil, salt, pepper, flour, common spices) and store them as assumed-available, so they don't count as "missing" when ranking recipes. This mirrors Spoonacular's `ignorePantry` option, which skips typical pantry items such as water, salt, and flour when matching ingredients.

---

## Paper 2: FoodLMM: A Versatile Food Assistant Using Large Multi-Modal Model

### 1. Full Citation & Link

Yin, Y., Qi, H., Zhu, B., Chen, J., Jiang, Y.-G., & Ngo, C.-W. (2025). FoodLMM: A versatile food assistant using large multi-modal model. *IEEE Transactions on Multimedia, 27*, 6949–6961. https://doi.org/10.1109/TMM.2025.3590924

**Link:** https://doi.org/10.1109/TMM.2025.3590924 · Open preprint: https://arxiv.org/abs/2312.14991 · Code: https://github.com/YuehaoYin/FoodLMM

### 2. Structured Summary

**Research problem.** General-purpose large multimodal models (LMMs) perform well on everyday vision-language tasks but remain unsatisfactory in specialized domains such as food, and earlier food models each handled only a single task. **Methodology.** Yin et al. present FoodLMM, built on the LISA architecture (the LLaVA multimodal model combined with the SAM segmentation model) and extended with task-specific tokens and heads that let it output nutrition values and multiple segmentation masks. Training has two stages: multi-task instruction tuning on public food benchmarks (including Food-101, VIREO Food-172, Recipe1M, Nutrition5k, and FoodSeg103), then fine-tuning on two GPT-4-generated datasets, *FoodDialogues* for multi-round conversation and *FoodReasonSeg* for reasoning-based segmentation. **Main findings.** A single model handled food classification, ingredient recognition, recipe generation, nutrition estimation, referring segmentation, and reasoning segmentation, and the authors report state-of-the-art results on each task. For example, on referring segmentation it improved cIoU on FoodSeg103 from 0.65 (LISA) to 0.78.

### 3. Three Key Insights

1. **General models still need domain checking.** Even strong LMMs are not food experts, and fine-grained distinctions such as scallions vs. leeks or Greek yogurt vs. sour cream are exactly where they slip. Before trusting any hosted model, we should benchmark it on *our own* labeled fridge photos.
2. **Numbers deserve dedicated outputs, not free text.** FoodLMM predicts nutrition through dedicated regression tokens and heads rather than asking the language model to write numbers as text. This supports a RecipeRAG-wide rule: numbers come from structured sources or specialized tools, never from free-form generation.
3. **Structured data can be turned into realistic conversations.** Using GPT-4 to convert structured nutrition records into multi-turn dialogues is a cheap way to create training and test data. We can do the same, turning recipe metadata and synthetic user profiles into conversational test cases for our evaluation harness.

### 4. Two Limitations or Risks

1. **Benchmarks show clean food, not cluttered kitchens.** The datasets behind FoodLMM mostly show single dishes or food items in relatively clean photos, not crowded shelves with packaging, glare, and occlusion. Reported accuracy likely overstates what to expect on real fridge photos, which is our core use case.
2. **Synthetic teacher data and heavy deployment.** Part of the fine-tuning data is generated by GPT-4, so the teacher model's errors and biases can be baked into a supposedly expert "food assistant." A model that combines an LMM with a segmentation backbone also needs dedicated GPU serving, which is beyond a student team's budget, so in practice we will call a hosted general-purpose multimodal model and must compensate for its weaker food expertise.

### 5. One Concrete Inspiration for RecipeRAG

**Two-pass pantry perception: detect, verify, then confirm.** In the first pass, the vision agent asks a hosted multimodal LLM for schema-validated JSON (`name`, `canonical_ingredient`, `quantity_estimate`, `confidence`, `location` such as "top shelf, left"). In the second pass, a focused prompt re-examines only low-confidence items ("Is the white tub on the top shelf yogurt, sour cream, or cream cheese?"). Anything still uncertain appears to the user as a one-tap confirmation chip. Following FoodLMM's lesson about dedicated outputs, the vision step never estimates nutrition; nutrition comes only from recipe data.

---

## Paper 3: Yum-me: A Personalized Nutrient-Based Meal Recommender System

### 1. Full Citation & Link

Yang, L., Hsieh, C.-K., Yang, H., Pollak, J. P., Dell, N., Belongie, S., Cole, C., & Estrin, D. (2017). Yum-me: A personalized nutrient-based meal recommender system. *ACM Transactions on Information Systems, 36*(1), Article 7. https://doi.org/10.1145/3072614

**Link:** https://doi.org/10.1145/3072614 · Free full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC6242282/ · Code: https://github.com/ylongqi/yumme

### 2. Structured Summary

**Research problem.** Nutrient-based meal recommendations could help people prevent or manage conditions such as diabetes and obesity, but they must also appeal to each person's palate, and existing preference elicitation was either too coarse (onboarding surveys) or too slow and burdensome (food journaling). **Methodology.** Yang et al. built Yum-me, which learns fine-grained food preferences through a visual quiz in which users choose among food photos, then projects that profile onto meals that fit the user's nutritional goals and dietary restrictions. The system relies on FoodDist, an open-source food-image embedding model benchmarked on Food-101, and a novel online learning framework that updates preferences from item-wise and pairwise image comparisons. The recipe pool consisted of about 50,000 main dishes collected through the Yummly API, grouped by diet type (no restriction, vegetarian, vegan, kosher, and halal). **Main findings.** In a field study with 227 anonymous users, the online learning framework outperformed baseline methods by a significant margin. In an end-to-end user study with 60 participants, Yum-me improved the recommendation acceptance rate by 42.63%.

### 3. Three Key Insights

1. **People can show their taste faster than they can describe it.** A few image choices captured fine-grained preferences that multiple-choice onboarding questions miss, without requiring users to keep a food diary. Visual elicitation is a practical answer to the cold-start problem.
2. **Goals filter; taste ranks.** Yum-me first restricts the pool to nutritionally appropriate options and then orders them by predicted preference. RecipeRAG uses the same division of labor: hard constraints and nutrition goals narrow the pool, and learned taste decides the order.
3. **Embeddings let a few choices generalize.** Because FoodDist places visually similar dishes close together, a handful of quiz answers generalizes to thousands of recipes. Our ranker can use recipe embeddings the same way, generalizing from a few likes to the whole catalog.

### 4. Two Limitations or Risks

1. **Looking good is not tasting good.** Picking a photo measures *visual appeal*, which is shaped by food styling and photo quality, and it misses texture, spice tolerance, and smell. Users may also tap photos of dishes they would never actually cook, so visual signals should initialize the profile, not define it.
2. **A closed, static recipe pool and coarse goals.** Yum-me depended on recipes collected through the Yummly API, a service that has since shut down, and on coarse goals such as reducing, maintaining, or increasing calories, protein, and fat. It did not consider what users already had at home, and a 60-person study can't show whether acceptance turns into long-term changes in eating behavior.

### 5. One Concrete Inspiration for RecipeRAG

**A 60-second visual taste quiz at onboarding.** New users will see 8 rounds of two recipe photos, drawn to cover diverse cuisines and cooking styles, and tap the one they would rather eat, with a "neither" option. Each choice updates a taste vector in the same embedding space our ranker uses, so the very first session is already personalized, and the pantry photo narrows results further. Quiz images come from Spoonacular image URLs, which its terms allow us to store. In the Checkpoint 3 pilot, we will compare first-session acceptance rates with and without the quiz.
