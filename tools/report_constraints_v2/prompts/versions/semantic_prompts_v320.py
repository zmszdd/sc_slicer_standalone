"""semantic-v3.20: give the two remaining sequence_domain_fork defects a recipe.

After v3.19 the last failing case was ``sequence_domain_fork`` (0/10).  Bounded by
v3.19's 50 real samples, its 10 failures were one normalizable shape plus TWO
genuine defects, each on a different sample:

* 6/10: the precondition "block.chainid is read once at deployment" was encoded as
  the self-comparison ``domain_separator_chain_id == domain_separator_chain_id``.
  The prompt already forbade self-comparisons but never said what a "value is read
  once / fixed / cached" fact SHOULD look like, so the model had no positive form
  to reach for.  v3.20 names the two faithful forms.  Verified offline against that
  real sample: encoding it as a sort:"bool" occurrence symbol named after its own
  source ID validates.
* 3/10: for ``state_correspondence`` the relation was the two-observable equality
  ``domain_separator_chain_id == current_chain_id``.  Audit item 4 tells the model to
  use exactly such an equality, but those observables are sourced from preconditions,
  so the equality alone leaves the selected impact uncited and
  ``classified_relation_alignment`` rejects it.  The model had in fact declared the
  impact-carrying ``signature_valid`` and then never referenced it.  v3.20 states
  that the correspondence alone is not enough and gives the shape that keeps it
  (relation as an any_of over the correspondence and the impact observable) --
  verified offline against that real sample: it validates.

Both additions live in the final mechanical audit, and neither relaxes a validator.
"""
import semantic_prompts_v319 as v319


PROMPT_VERSION = 'semantic-v3.20'

# v3.19 audit item 3: banned the self-comparison but gave no positive form.
_LEGACY_TERM_RULE = """3. Every selected precondition_id has exactly one precondition_terms entry. If a
   selected fact cannot be represented faithfully, move it to assumptions and do
   not keep it in precondition_ids.
   Never satisfy this requirement with x==x, x!=x, x<=x, x>=x or another
   self-comparison; such a predicate carries no report information."""

_FIXED_TERM_RULE = """3. Every selected precondition_id has exactly one precondition_terms entry. If a
   selected fact cannot be represented faithfully, move it to assumptions and do
   not keep it in precondition_ids.
   Never satisfy this requirement with x==x, x!=x, x<=x, x>=x or another
   self-comparison; such a predicate carries no report information. A fact that
   says a value is fixed, cached, or read once does have a faithful form: compare
   it against the observable holding the other value, or declare a sort:"bool"
   occurrence symbol for the event and name it after this source ID. Move the
   fact to assumptions only when neither form exists."""

# v3.19 audit item 4: prescribed the equality without saying it must cite the impact.
_LEGACY_CORRESPONDENCE_RULE = """4. Check that relation_class is compatible with pattern. In particular,
   state_correspondence uses relation_obligation with observable equality/inequality;
   monotonicity uses the monotonicity pattern. Never bend a class's fixed kind merely to
   fit the prose of a desired event field."""

_FIXED_CORRESPONDENCE_RULE = """4. Check that relation_class is compatible with pattern. In particular,
   state_correspondence uses relation_obligation with observable equality/inequality;
   monotonicity uses the monotonicity pattern. Never bend a class's fixed kind merely to
   fit the prose of a desired event field. The correspondence observables are
   sourced from preconditions, so the correspondence ALONE leaves the selected
   impact uncited: when the intent names a purpose clause that the impact is the
   failure of, relation MUST also include the observable carrying that impact, for
   example relation as an any_of over the correspondence and that observable.
   Carrying the impact on a symbol that never appears in relation does not count."""

FORMAL_PLAN_PROMPT = (v319.FORMAL_PLAN_PROMPT
                      .replace(_LEGACY_TERM_RULE, _FIXED_TERM_RULE)
                      .replace(_LEGACY_CORRESPONDENCE_RULE, _FIXED_CORRESPONDENCE_RULE))
ID_FORMAL_PROMPT = FORMAL_PLAN_PROMPT
FORMAL_PROMPT = FORMAL_PLAN_PROMPT
CORE_SCOPE = v319.CORE_SCOPE
FULL_SCOPE = CORE_SCOPE
ID_ELEMENT_PROMPT = v319.ID_ELEMENT_PROMPT.replace('semantic-v3.19', PROMPT_VERSION)
ELEMENT_PROMPT = v319.ELEMENT_PROMPT.replace('semantic-v3.19', PROMPT_VERSION)


def formal_prompt(evidence_mode, scope):
    if evidence_mode != 'ids' or scope != 'core':
        raise ValueError('semantic-v3.20 supports ID/core mode only')
    return FORMAL_PLAN_PROMPT.removesuffix('DATA:\n') + CORE_SCOPE + '\nDATA:\n'
