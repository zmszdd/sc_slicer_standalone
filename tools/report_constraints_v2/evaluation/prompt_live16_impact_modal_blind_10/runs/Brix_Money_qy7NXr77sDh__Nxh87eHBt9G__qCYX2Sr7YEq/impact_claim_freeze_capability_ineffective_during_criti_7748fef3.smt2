; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c735c1f4d_freeze_capability_effective () Bool)
(declare-fun c735c1f4d_user_assets_in_cooldown () Bool)
(declare-fun c735c1f4d_user_has_full_restricted_role () Bool)
(assert
 (= c735c1f4d_freeze_capability_effective c735c1f4d_freeze_capability_effective))
(assert
 (= c735c1f4d_user_assets_in_cooldown c735c1f4d_user_assets_in_cooldown))
(assert
 (= c735c1f4d_user_has_full_restricted_role c735c1f4d_user_has_full_restricted_role))
(define-fun report_preconditions () Bool (and c735c1f4d_user_assets_in_cooldown c735c1f4d_user_has_full_restricted_role))
(define-fun report_safety () Bool (=> (and c735c1f4d_user_assets_in_cooldown
         c735c1f4d_user_has_full_restricted_role)
    c735c1f4d_freeze_capability_effective))
(define-fun report_effects () Bool (and c735c1f4d_user_assets_in_cooldown
     c735c1f4d_user_has_full_restricted_role
     (not c735c1f4d_freeze_capability_effective)))
