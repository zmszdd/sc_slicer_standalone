; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c576698af_deposit_fee_deducted () Bool)
(declare-fun c576698af_dispute_deposit_occurred () Bool)
(declare-fun c576698af_disputer_stuck_observed () Bool)
(declare-fun c576698af_fot_token_is_dispute_token () Bool)
(declare-fun c576698af_resolve_completed () Bool)
(assert
 (= c576698af_deposit_fee_deducted c576698af_deposit_fee_deducted))
(assert
 (= c576698af_dispute_deposit_occurred c576698af_dispute_deposit_occurred))
(assert
 (= c576698af_disputer_stuck_observed c576698af_disputer_stuck_observed))
(assert
 (= c576698af_fot_token_is_dispute_token c576698af_fot_token_is_dispute_token))
(assert
 (= c576698af_resolve_completed c576698af_resolve_completed))
(define-fun report_preconditions () Bool (and c576698af_fot_token_is_dispute_token
     c576698af_dispute_deposit_occurred
     c576698af_deposit_fee_deducted))
(define-fun report_safety () Bool (=> (and c576698af_fot_token_is_dispute_token
         c576698af_dispute_deposit_occurred
         c576698af_deposit_fee_deducted)
    (and c576698af_resolve_completed (not c576698af_disputer_stuck_observed))))
(define-fun report_effects () Bool (and c576698af_fot_token_is_dispute_token
     c576698af_dispute_deposit_occurred
     c576698af_deposit_fee_deducted
     (not (and c576698af_resolve_completed
               (not c576698af_disputer_stuck_observed)))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
