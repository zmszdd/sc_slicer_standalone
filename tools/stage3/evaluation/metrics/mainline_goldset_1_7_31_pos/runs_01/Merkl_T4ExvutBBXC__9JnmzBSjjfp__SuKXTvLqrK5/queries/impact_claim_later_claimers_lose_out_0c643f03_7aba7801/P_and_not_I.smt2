; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c27a7a93e_actual_received () Int)
(declare-fun c27a7a93e_credited_balance () Int)
(declare-fun c27a7a93e_fot_token_whitelisted () Bool)
(declare-fun c27a7a93e_later_claimers_lose_out () Bool)
(declare-fun c27a7a93e_transfer_amount_received () Int)
(declare-fun c27a7a93e_transfer_amount_requested () Int)
(assert
 (= c27a7a93e_actual_received c27a7a93e_actual_received))
(assert
 (= c27a7a93e_credited_balance c27a7a93e_credited_balance))
(assert
 (= c27a7a93e_fot_token_whitelisted c27a7a93e_fot_token_whitelisted))
(assert
 (= c27a7a93e_later_claimers_lose_out c27a7a93e_later_claimers_lose_out))
(assert
 (= c27a7a93e_transfer_amount_received c27a7a93e_transfer_amount_received))
(assert
 (= c27a7a93e_transfer_amount_requested c27a7a93e_transfer_amount_requested))
(define-fun report_preconditions () Bool (and c27a7a93e_fot_token_whitelisted
     (< c27a7a93e_transfer_amount_received c27a7a93e_transfer_amount_requested)))
(define-fun report_safety () Bool (=> c27a7a93e_fot_token_whitelisted
    (= c27a7a93e_credited_balance c27a7a93e_actual_received)))
(define-fun report_effects () Bool (and c27a7a93e_fot_token_whitelisted
     (not (= c27a7a93e_credited_balance c27a7a93e_actual_received))
     c27a7a93e_later_claimers_lose_out))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
