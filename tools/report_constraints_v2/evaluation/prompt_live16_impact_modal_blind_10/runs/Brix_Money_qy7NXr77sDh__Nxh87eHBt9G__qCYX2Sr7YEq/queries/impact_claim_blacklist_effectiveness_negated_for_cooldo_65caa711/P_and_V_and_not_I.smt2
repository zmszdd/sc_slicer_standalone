; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c906d19ce_blacklist_effective_for_cooldown_funds () Bool)
(declare-fun c906d19ce_user_assets_in_cooldown () Bool)
(declare-fun c906d19ce_user_has_full_restricted_staker_role () Bool)
(assert
 (= c906d19ce_blacklist_effective_for_cooldown_funds c906d19ce_blacklist_effective_for_cooldown_funds))
(assert
 (= c906d19ce_user_assets_in_cooldown c906d19ce_user_assets_in_cooldown))
(assert
 (= c906d19ce_user_has_full_restricted_staker_role c906d19ce_user_has_full_restricted_staker_role))
(define-fun report_preconditions () Bool (and c906d19ce_user_assets_in_cooldown
     c906d19ce_user_has_full_restricted_staker_role))
(define-fun report_safety () Bool (=> (and c906d19ce_user_assets_in_cooldown
         c906d19ce_user_has_full_restricted_staker_role)
    c906d19ce_blacklist_effective_for_cooldown_funds))
(define-fun report_effects () Bool (and c906d19ce_user_assets_in_cooldown
     c906d19ce_user_has_full_restricted_staker_role
     (not c906d19ce_blacklist_effective_for_cooldown_funds)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
