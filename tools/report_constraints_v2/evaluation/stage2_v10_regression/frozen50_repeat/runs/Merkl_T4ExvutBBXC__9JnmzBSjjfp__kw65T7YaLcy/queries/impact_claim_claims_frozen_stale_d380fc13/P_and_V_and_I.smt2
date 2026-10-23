; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c310d2fc2_claims_frozen_stale () Bool)
(declare-fun c310d2fc2_dispute_amount_sent_tokens () Int)
(declare-fun c310d2fc2_fot_fee_tokens () Int)
(declare-fun c310d2fc2_fot_token_is_dispute_token () Bool)
(declare-fun c310d2fc2_recovery_via_recover_erc20_possible () Bool)
(declare-fun c310d2fc2_resolve_dispute_succeeds () Bool)
(assert
 (= c310d2fc2_claims_frozen_stale c310d2fc2_claims_frozen_stale))
(assert
 (= c310d2fc2_dispute_amount_sent_tokens c310d2fc2_dispute_amount_sent_tokens))
(assert
 (= c310d2fc2_fot_fee_tokens c310d2fc2_fot_fee_tokens))
(assert
 (= c310d2fc2_fot_token_is_dispute_token c310d2fc2_fot_token_is_dispute_token))
(assert
 (= c310d2fc2_recovery_via_recover_erc20_possible c310d2fc2_recovery_via_recover_erc20_possible))
(assert
 (= c310d2fc2_resolve_dispute_succeeds c310d2fc2_resolve_dispute_succeeds))
(define-fun report_preconditions () Bool (and c310d2fc2_fot_token_is_dispute_token
     (= 1000 c310d2fc2_dispute_amount_sent_tokens)
     (= 10 c310d2fc2_fot_fee_tokens)
     (not c310d2fc2_recovery_via_recover_erc20_possible)))
(define-fun report_safety () Bool (=> (and c310d2fc2_fot_token_is_dispute_token
         (= 1000 c310d2fc2_dispute_amount_sent_tokens)
         (= 10 c310d2fc2_fot_fee_tokens)
         (not c310d2fc2_recovery_via_recover_erc20_possible))
    (and c310d2fc2_resolve_dispute_succeeds (not c310d2fc2_claims_frozen_stale))))
(define-fun report_effects () Bool (and c310d2fc2_fot_token_is_dispute_token
     (= 1000 c310d2fc2_dispute_amount_sent_tokens)
     (= 10 c310d2fc2_fot_fee_tokens)
     (not c310d2fc2_recovery_via_recover_erc20_possible)
     (not (and c310d2fc2_resolve_dispute_succeeds
               (not c310d2fc2_claims_frozen_stale)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
