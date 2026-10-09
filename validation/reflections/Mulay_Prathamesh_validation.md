CP2 Validation Findings and Design Implications
Prompting Study
Platforms Tested
Platform	Model	Date Tested	Scenarios Run	Coverage
ChatGPT	GPT-4o	Oct. 7–8, 2026	12 / 12	Full study
Gemini	Gemini 1.5 Pro	Oct. 7–8, 2026	5 / 12	T01, T04, T05, T09, T10
Important: The two platforms were not tested on an identical set of scenarios. ChatGPT was used for all 12 scenarios, while Gemini was used for a subset of 5 scenarios. Therefore, the comparison is directional rather than a complete head-to-head benchmark.
Scenario Results
ID	Scenario	ChatGPT (GPT-4o)	Gemini 1.5 Pro	Key Observation
T01	Typical receipt extraction	Pass	Pass	Both extracted the receipt conservatively without inventing quantities.

T02	Abbreviated receipt	Partial	Partial	Both resolved ambiguity; ChatGPT promoted a likely count, while Gemini did not flag the ambiguity.

T03	Unknown package size	Pass	—	ChatGPT handled the unknown quantity appropriately.

T04	Multi-turn dietary constraint	Pass	Pass	Both maintained the dietary constraint across the interaction.

T05	Explicit exclusion: no chicken	Pass	Pass	Both respected the explicit exclusion; ChatGPT may also have used account memory.

T06	Missing core ingredient	Pass	—	ChatGPT correctly treated the missing core ingredient as important.

T07	Optional lemon	Pass	—	ChatGPT did not treat the optional ingredient as recipe-blocking.

T08	Sour cream substitution	Partial	—	ChatGPT approved a substitution without recipe context and introduced an invented recipe context.

T09	Inventory decision rights	Pass	Partial	ChatGPT distinguished purchased quantity from current inventory; Gemini would update inventory automatically unless explicitly instructed otherwise.

T10	Constraint overload	Partial	Partial	Both retained some constraints but dropped or assumed details under multiple simultaneous constraints.

T11	Stale inventory	Partial	—	ChatGPT removed spinach but still treated oil as available, showing that conversational memory and structured inventory can diverge.

T12	Source faithfulness	Pass	—	ChatGPT stayed faithful to the provided source information.


Platform-Level Takeaway
Platform	Strength Observed	Main Failure/Risk Observed
ChatGPT	Strong overall instruction following and inventory/constraint reasoning	Can invent context during substitution and can mix conversational context with inventory state
Gemini	Conservative behavior in some receipt and substitution-related cases	Can make incorrect assumptions about inventory ownership and can drop constraints under overload



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

=====================================================

Class Storyboard
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/e58ef8d2-e9eb-40b9-b62c-9a715deae482" />
