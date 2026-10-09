CP2 Validation Findings and Design Implications
Prompting Study
Platforms Tested
- ChatGPT (GPT-4o) --- primary platform, 7--8 Oct 2026
- Gemini 1.5 Pro --- secondary platform; outputs are documented in
  validation/transcripts/gemini_outputs.md
Scenarios Run
All twelve scenarios in validation/PROMPTING_PROTOCOL.md were run on
ChatGPT. Gemini was run on a focused subset (T01, T04, T05, T09, T10)
for cross-platform comparison.
  Scenario       Type           Pillar              ChatGPT result    Gemini result
  T01 ---        typical        reasoning           Pass --- did  Pass ---
  Typical                                           not invent        similar
  receipt                                           quantities        conservative
  extraction                                                          output
  T02 ---        edge           reasoning           Partial ---   Partial ---
  Abbreviated                                       merged "whole"    resolved
  receipt                                           and "2%," and     ambiguity
                                                    promoted a likely without
                                                    count             flagging it
  T03 ---        edge           reasoning           Pass ---      Pass
  Unknown                                           asked for
  package size                                      confirmation      
  T04 ---        typical        memory              Pass ---      Pass ---
  Multi-turn                                        retained          retained
  dietary                                           vegetarian,       constraints
  constraint                                        protein, and time
                                                    constraints
                                                    across turns      
  T05 ---        failure        memory              Pass --- kept Pass
  Explicit                                          chicken out;
  exclusion (no                                     account memory
  chicken)                                          may have
                                                    influenced the
                                                    response          
  T06 ---        failure        reasoning           Pass ---      Not tested
  Missing core                                      flagged chicken
  ingredient                                        as missing        
  T07 ---        edge           reasoning           Pass ---      Not tested
  Optional                                          correctly treated
  ingredient (no                                    lemon as optional
  lemon)                                                              
  T08 ---        edge           reasoning           Partial ---   Not tested
  Substitution                                      approved the swap
  (sour cream                                       without asking
  for yogurt)                                       which recipe and
                                                    invented a
                                                    chicken rice bowl
                                                    context           
  T09 ---        failure        meta-coordination   Pass ---      Partial ---
  Inventory                                         stated that       said it would
  decision                                          purchased 2 lb    update
  rights                                            does not          inventory
                                                    necessarily mean  automatically
                                                    2 lb is currently unless told
                                                    on hand           otherwise
  T10 ---        edge           attention           Partial ---   Partial ---
  Constraint                                        retained salient  dropped "no
  overload                                          constraints but   mushrooms" from
                                                    claimed ~15      the output
                                                    minutes while
                                                    assuming cooked
                                                    rice              
  T11 --- Stale  failure        memory              Partial ---   Not tested
  inventory                                         removed spinach
                                                    from
                                                    recommendations
                                                    but still listed
                                                    oil as available  
  T12 --- Source edge           reasoning           Pass ---      Not tested
  faithfulness                                      listed missing
                                                    ingredients
                                                explicitly        
Key Failure Cases
- T08 --- Ambiguous substitution: ChatGPT approved sour cream as a
  substitute for Greek yogurt and introduced a chicken rice bowl that
  was not in the prompt. This is a reasoning failure: the model
  closed an ambiguous context by inventing one rather than asking for
  the missing context.
- T09 --- Inventory ownership: Gemini said it would update
  inventory automatically from a receipt unless told otherwise. This
  is a meta-coordination failure: the AI assumed it owned pantry
  truth rather than recognizing that the user owns the inventory
  decision.
- T10 --- Constraint overload: Gemini dropped "no mushrooms" from
  an eight-constraint prompt and produced a recipe containing
  mushrooms. This is an attention failure: a lower-salience
  constraint was lost in a dense instruction set.
- T11 --- Stale inventory: ChatGPT removed spinach from active
  recommendations but still listed oil as an available ingredient in
  the same response. This shows that conversational context and
  structured inventory state are not necessarily the same thing.
Speed-Dating Interviews
Interview 5 --- Beginner Cook, Low Confidence
- Participant: Young professional who recently started cooking and
  generally follows recipes exactly.
- Task shown: A substitution suggestion: sour cream offered in
  place of Greek yogurt, matching prompting scenario T08.
- Main finding: Beginners may accept substitutions they cannot
  independently evaluate. The participant liked substitutions because
  buying a whole ingredient for one recipe feels wasteful, but had no
  reliable way to judge whether a swap was appropriate.
- Quote: "If the app tells me sour cream works instead of yogurt,
  I probably won't know enough to question it."
- Complementarity interpretation: The hybrid only outperforms
  AI-alone when the human can catch or evaluate what the AI gets
  wrong. For substitutions, this beginner could not. Without
  additional support, the hybrid effectively becomes AI-alone at
  exactly the point where the AI is uncertain.
- Trust-calibration implication: Users may interpret the model's
  confidence as evidence of correctness. The interface therefore needs
  to make uncertainty and trade-offs visible.
- Design implication: Label substitutions as safe, possible, or
  not recommended; explain what changes (for example, flavor,
  texture, or protein); and ask which recipe the substitution applies
  to before approving it.
Interview 6 --- Minimal Kitchen Equipment
- Participant: College student in a small apartment with one pan,
  one pot, a microwave, and no oven.
- Task shown: Recipe recommendations from a pantry containing the
  required ingredients.
- Main finding: A recipe is not feasible if it requires equipment
  the user does not own, even when all required ingredients are
  available. The participant also preferred three strong options over
  a long list and did not want to re-enter equipment information for
  every request.
- Quote: "Having all the ingredients doesn't help if the recipe
  suddenly tells me to put something in an oven."
- Complementarity interpretation: This reveals a
  knowledge-infrastructure gap. The AI cannot reliably assess kitchen
  feasibility if the kitchen is not represented in the system. Without
  stored equipment information, the user may discover the problem only
  after starting the recipe.
- Design implication: Equipment should be part of the feasibility
  check. A recipe requiring unavailable equipment should be blocked as
  not feasible, rather than merely ranked lower. The design should
  store equipment in a saved kitchen profile so it is entered once.
Finding That Changed My Assumption
Initial Assumption
My hypothesis-evolution table initially treated a confident substitution
as helpful: it could save a grocery trip, and beginners might benefit
because they are less likely to know substitutions themselves.
What Changed It
Interview 5 and T08 changed that assumption when considered together.
The beginner said plainly that they would not know enough to question a
substitution. In T08, ChatGPT responded that sour cream could be used
for Greek yogurt even though it did not know which recipe was involved.
One response variant also introduced a "chicken rice bowl" that was not
present in the prompt. Gemini, by contrast, responded more cautiously
and asked for the recipe context.
The key insight is that the helpfulness of a substitution depends on the
user's ability to evaluate it. The users most likely to benefit from
substitution help may also be the least able to judge whether the
recommendation is sound.
Connection to the Human--AI Complementarity Lens
The working theory is that ChefNova should outperform human-alone and
AI-alone when the system deliberately assigns different parts of the
task to the human and AI.
- Complementarity: For a beginner, substitution is a task where
  the human may not have enough domain knowledge to provide the needed
  check. If the AI simply decides the swap, the hybrid becomes
  AI-alone with extra steps. The design must therefore give the human
  enough information to meaningfully participate in the decision.
- Trust calibration: The beginner may use the answer's confidence
  as a signal of correctness. In T08, the confidence was not supported
  by sufficient context because the model did not know which recipe
  was involved. The fix is to expose uncertainty and trade-offs rather
  than presenting an ambiguous swap as a simple "yes."
- Shared mental model: "Sour cream works instead of yogurt" may be
  interpreted by a beginner as "the result will be the same." The
  model may instead mean that it is workable only in certain savory
  contexts and will change texture, flavor, or nutritional properties.
  The interface should place those trade-offs next to the substitution
  label.
- Reasoning: T08 is a reasoning scenario. The failure was not
  necessarily a wrong fact; it was the decision to close an ambiguous
  context with an unsupported assumption. Because the two platforms
  behaved differently on the same prompt, "ask first" should be
  designed into the workflow rather than left to whichever model is
  underneath.
An Assumption That Was Confirmed
shared-apartment case made the issue stronger: a receipt can describe
groceries that were never actually the user's. This reinforces the
design principle that receipt data is evidence of purchase, while
user-confirmed inventory is the source of truth.
How This Affected the Design
1. Substitution confidence became a P1 requirement.
   OPPORTUNITY_FRAMING.md now prioritizes substitution confidence
   based on Interview 5 and T08. DESIGN_SPEC.md §8 requires every
   substitution to be labeled safe, possible, or not recommended
   and to state what changes, such as flavor, texture, or protein.
2. Substitution became an interrogation moment. DESIGN_SPEC.md
   §10 specifies that ChefNova should ask for clarification when a
   substitution has meaningful uncertainty. In practice, ChefNova
   should ask which recipe the swap is for before approving it. This
   matches the more cautious behavior observed from Gemini on T08.
3. Decision rights are explicit. In DESIGN_SPEC.md §4, the
   decision "Is a substitution acceptable?" is assigned as AI
   proposes; user decides. The model can suggest a swap but cannot
   silently apply it to the recipe.
4. Built vs. specified is explicit. The current prototype only
   displays a caution that suggested swaps are possible rather than
   guaranteed safe substitutions. The three-level label and clarifying
   question are specified for CP3 but are not yet fully implemented.
CP3 Test
The most direct claim to test in CP3 is whether substitution labels
change what beginners accept.
A controlled test could give beginners the same questionable
substitution under two interface conditions:
1. Without the label and trade-off information
2. With the safe/possible/not-recommended label and explicit
   trade-off information
Measure how often participants accept, reject, or question the
substitution.
This directly tests whether ChefNova's interface restores the human's
role in the decision rather than encouraging passive acceptance of AI
output.
Summary for CP3
The CP2 evidence points to a broader design principle:
ChefNova should not simply make recommendations; it should structure
the interaction so the AI handles scalable reasoning and consistency
checks while the user retains meaningful decision authority.

For CP3, the key question is whether these design changes produce a
measurable advantage over human-alone and AI-alone on the same
decision tasks.
Reference
Gonzalez, C., et al. (2026). Toward a science of human--AI teaming for
decision making: A complementarity framework. PNAS Nexus, 5(3),
pgag030.

Class Storyboard
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/e58ef8d2-e9eb-40b9-b62c-9a715deae482" />
