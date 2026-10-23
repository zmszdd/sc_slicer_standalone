; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd370564d_claim_payout_completed () Bool)
(declare-fun cd370564d_clear_or_redirect_path_available () Bool)
(declare-fun cd370564d_user_blacklisted_before_claim () Bool)
(assert
 (= cd370564d_claim_payout_completed cd370564d_claim_payout_completed))
(assert
 (= cd370564d_clear_or_redirect_path_available cd370564d_clear_or_redirect_path_available))
(assert
 (= cd370564d_user_blacklisted_before_claim cd370564d_user_blacklisted_before_claim))
(define-fun report_preconditions () Bool cd370564d_user_blacklisted_before_claim)
(define-fun report_safety () Bool (=> (not cd370564d_clear_or_redirect_path_available)
    (=> cd370564d_user_blacklisted_before_claim
        cd370564d_claim_payout_completed)))
(define-fun report_effects () Bool (and (not cd370564d_clear_or_redirect_path_available)
     cd370564d_user_blacklisted_before_claim
     (not cd370564d_claim_payout_completed)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
