# Paper 1: Inverse Cooking: Recipe Generation from Food Images

### 1. Full Citation & Link

Salvador, A., Drozdzal, M., Giró-i-Nieto, X., & Romero, A. (2019). Inverse cooking: Recipe generation from food images. In *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)* (pp. 10453–10462). IEEE. [https://doi.org/10.1109/CVPR.2019.01070](https://doi.org/10.1109/CVPR.2019.01070)

**Link:** [https://openaccess.thecvf.com/content_CVPR_2019/html/Salvador_Inverse_Cooking_Recipe_Generation_From_Food_Images_CVPR_2019_paper.html](https://openaccess.thecvf.com/content_CVPR_2019/html/Salvador_Inverse_Cooking_Recipe_Generation_From_Food_Images_CVPR_2019_paper.html) · Preprint: [https://arxiv.org/abs/1812.06164](https://arxiv.org/abs/1812.06164) · Code: https://github.com/facebookresearch/inversecooking

### 2. Structured Summary

**Research problem.** Food images contain rich information about ingredients and preparation, but earlier image-to-recipe systems mostly *retrieved* existing recipes from a fixed dataset, an approach that fails whenever no matching recipe exists. **Methodology.** Salvador et al. instead generate a complete recipe from a single food image in two stages. First, the model predicts the ingredients as an unordered set, using an architecture that models dependencies among ingredients without imposing an order on them. Second, a transformer generates cooking instructions by attending to both the image and the predicted ingredients; the full system is trained and evaluated on the large-scale Recipe1M dataset. **Main findings.** The approach improved ingredient prediction over previous baselines and produced high-quality recipes. In a human evaluation, its generated recipes were judged more compelling than those returned by retrieval-based approaches.

### 3. Three Key Insights

1. **Ingredients are a set, not a sequence.** Modeling ingredients as an unordered set means a model isn't penalized for listing "garlic, onion" instead of "onion, garlic." For ChefNova, the broader lesson is that extracted grocery items should be evaluated as structured ingredient records rather than as a fixed sequence of text.

2. **Separate extraction from recipe reasoning.** Splitting "what was purchased" from "what to cook" makes each stage easier to evaluate independently. ChefNova will first convert a receipt or grocery-order screenshot into structured ingredient data, then use that confirmed inventory as input to recipe recommendation and reasoning.

3. **Structured ingredients are a reusable bridge.** Once a receipt or grocery-order screenshot becomes a clean set of normalized ingredients, that information can support recipe retrieval, ingredient checking, substitutions, and missing-item lists. The extraction agent should therefore output structured ingredient records rather than an unconstrained description of the image.

### 4. Two Limitations or Risks

1. **Receipt formats differ substantially from benchmark images.** Grocery receipts and online-order screenshots can vary in layout, abbreviations, image quality, and naming conventions across stores. This means extraction accuracy cannot simply be assumed from general multimodal benchmarks and should instead be evaluated on representative receipt and order examples.

2. **Generated recipes are unverified.** Instructions generated from an image can be plausible but untested, with no guarantees about quantities, cooking safety (for example, safe internal temperatures for meat), or allergens. That is acceptable for research but not for a consumer product that tells people what to eat.

### 5. One Concrete Inspiration for ChefNova

**Structured grocery extraction with user confirmation.** Our multimodal agent will convert grocery receipts or online grocery order screenshots into structured ingredient records containing the normalized ingredient name, quantity, and unit. Because a purchase does not prove that an item is still available, extracted items will be presented to the user for review and correction before being saved to the pantry. This separates visual extraction from authoritative inventory state and gives us a concrete way to evaluate extraction accuracy.


---

# Paper 2: FoodLMM: A Versatile Food Assistant Using Large Multi-Modal Model

### 1. Full Citation & Link

Yin, Y., Qi, H., Zhu, B., Chen, J., Jiang, Y.-G., & Ngo, C.-W. (2025). FoodLMM: A versatile food assistant using large multi-modal model. *IEEE Transactions on Multimedia, 27*, 6949–6961. [https://doi.org/10.1109/TMM.2025.3590924](https://doi.org/10.1109/TMM.2025.3590924)

**Link:** [https://doi.org/10.1109/TMM.2025.3590924](https://doi.org/10.1109/TMM.2025.3590924) · Open preprint: [https://arxiv.org/abs/2312.14991](https://arxiv.org/abs/2312.14991) · Code: https://github.com/YuehaoYin/FoodLMM

### 2. Structured Summary

**Research problem.** General-purpose large multimodal models (LMMs) perform well on everyday vision-language tasks but remain unsatisfactory in specialized domains such as food, and earlier food models each handled only a single task. **Methodology.** Yin et al. present FoodLMM, built on the LISA architecture (the LLaVA multimodal model combined with the SAM segmentation model) and extended with task-specific tokens and heads that let it output nutrition values and multiple segmentation masks. Training has two stages: multi-task instruction tuning on public food benchmarks (including Food-101, VIREO Food-172, Recipe1M, Nutrition5k, and FoodSeg103), then fine-tuning on two GPT-4-generated datasets, *FoodDialogues* for multi-round conversation and *FoodReasonSeg* for reasoning-based segmentation. **Main findings.** A single model handled food classification, ingredient recognition, recipe generation, nutrition estimation, referring segmentation, and reasoning segmentation, and the authors report state-of-the-art results on each task. For example, on referring segmentation it improved cIoU on FoodSeg103 from 0.65 (LISA) to 0.78.

### 3. Three Key Insights

1. **General models still need domain checking.** Even strong multimodal models can struggle with fine-grained food distinctions and messy real-world inputs. Before relying on a hosted model, ChefNova should benchmark its extraction performance on representative grocery receipts and online grocery-order screenshots from the intended use case.

2. **Numbers deserve dedicated outputs, not free text.** FoodLMM predicts nutrition through dedicated regression tokens and heads rather than asking the language model to write numbers as text. This supports a ChefNova design principle: quantities and units should come from structured data and validation logic rather than relying on free-form generation.

3. **Structured data can support realistic conversational testing.** Using structured recipe metadata and synthetic user profiles can help create realistic multi-turn test cases. ChefNova can use these cases to test whether constraints such as time, diet, protein goals, and dislikes are preserved throughout a conversation.

### 4. Two Limitations or Risks

1. **Benchmarks do not fully represent grocery inputs.** The datasets used by FoodLMM contain relatively controlled food images and task-specific benchmarks, while ChefNova will process receipts and online grocery screenshots with different layouts, abbreviations, image quality, and formatting. Reported benchmark performance therefore may not directly predict extraction accuracy in our use case.

2. **Synthetic teacher data and heavy deployment.** Part of the fine-tuning data is generated by GPT-4, so the teacher model's errors and biases can be incorporated into the resulting food assistant. A model that combines an LMM with a segmentation backbone also requires dedicated GPU serving, which is beyond a student team's budget. ChefNova will therefore use a hosted general-purpose multimodal model and compensate through structured outputs, validation, and user confirmation.

### 5. One Concrete Inspiration for ChefNova

**Two-stage receipt extraction and confirmation.** The multimodal model will first extract grocery items into structured fields such as `name`, `canonical_ingredient`, `quantity`, and `unit`. A validation step will flag ambiguous or low-confidence extractions for user review. The user can correct the item or quantity before it is added to the inventory. This follows FoodLMM's emphasis on structured outputs while keeping the final inventory state under user control.


---

# Paper 3: Yum-me: A Personalized Nutrient-Based Meal Recommender System

### 1. Full Citation & Link

Yang, L., Hsieh, C.-K., Yang, H., Pollak, J. P., Dell, N., Belongie, S., Cole, C., & Estrin, D. (2017). Yum-me: A personalized nutrient-based meal recommender system. *ACM Transactions on Information Systems, 36*(1), Article 7. [https://doi.org/10.1145/3072614](https://doi.org/10.1145/3072614)

**Link:** [https://doi.org/10.1145/3072614](https://doi.org/10.1145/3072614) · Free full text: [https://pmc.ncbi.nlm.nih.gov/articles/PMC6242282/](https://pmc.ncbi.nlm.nih.gov/articles/PMC6242282/) · Code: https://github.com/ylongqi/yumme

### 2. Structured Summary

**Research problem.** Nutrient-based meal recommendations could help people prevent or manage conditions such as diabetes and obesity, but they must also appeal to each person's palate, and existing preference elicitation was either too coarse (onboarding surveys) or too slow and burdensome (food journaling). **Methodology.** Yang et al. built Yum-me, which learns fine-grained food preferences through a visual quiz in which users choose among food photos, then projects that profile onto meals that fit the user's nutritional goals and dietary restrictions. The system relies on FoodDist, an open-source food-image embedding model benchmarked on Food-101, and a novel online learning framework that updates preferences from item-wise and pairwise image comparisons. The recipe pool consisted of about 50,000 main dishes collected through the Yummly API, grouped by diet type (no restriction, vegetarian, vegan, kosher, and halal). **Main findings.** In a field study with 227 anonymous users, the online learning framework outperformed baseline methods by a significant margin. In an end-to-end user study with 60 participants, Yum-me improved the recommendation acceptance rate by 42.63%.

### 3. Three Key Insights

1. **People can express preferences without lengthy forms.** Yum-me demonstrates that preference elicitation can be designed to reduce the burden of describing food preferences in detail. For ChefNova, the broader lesson is to let users express preferences and constraints naturally through conversation.

2. **Constraints should narrow recommendations before recipe selection.** Yum-me demonstrates the value of incorporating user goals and restrictions into recommendation rather than treating them as secondary preferences. ChefNova applies this principle by using constraints such as dietary preferences, preparation time, protein goals, dislikes, and available ingredients when determining which recipes are viable.

3. **Personalization should reduce user effort.** Yum-me shows that recommendation systems can learn useful preference information without requiring users to maintain detailed food journals. ChefNova applies the broader lesson through conversational preference capture, allowing users to express preferences and constraints naturally rather than requiring a lengthy preference questionnaire.

### 4. Two Limitations or Risks

1. **Visual preference does not necessarily represent actual cooking preferences.** Choosing an appealing food image may not capture factors such as taste, texture, cooking effort, ingredient availability, or willingness to prepare a particular meal. ChefNova therefore focuses on explicit conversational constraints and the user's current inventory rather than relying solely on visual preference signals.

2. **A closed, static recipe pool and coarse goals.** Yum-me depended on recipes collected through the Yummly API, a service that has since shut down, and on relatively coarse nutritional goals. It did not consider what users already had at home, which leaves an important gap for ChefNova: recommendations should consider both user preferences and the ingredients currently confirmed in their inventory.

### 5. One Concrete Inspiration for ChefNova

**Conversational preference and constraint refinement.** ChefNova can use natural-language interaction to capture multiple meal constraints such as dietary preference, preparation time, protein goals, and dislikes. Rather than requiring users to specify every preference through a rigid form, the system can refine these constraints through conversation and use them to narrow recipe options. This supports a more flexible recommendation experience while keeping the authoritative inventory state separate from the model.
