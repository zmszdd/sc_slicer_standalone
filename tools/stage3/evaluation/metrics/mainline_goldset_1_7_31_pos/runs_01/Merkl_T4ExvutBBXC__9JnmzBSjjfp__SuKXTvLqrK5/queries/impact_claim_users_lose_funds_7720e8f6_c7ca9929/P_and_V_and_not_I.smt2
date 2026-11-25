; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9128eb53_actual_token_holdings () Int)
(declare-fun c9128eb53_fot_token_is_whitelisted () Bool)
(declare-fun c9128eb53_recorded_creator_balance_total () Int)
(declare-fun c9128eb53_transfer_received_amount () Int)
(declare-fun c9128eb53_transfer_requested_amount () Int)
(declare-fun c9128eb53_users_lose_funds_occurred () Bool)
(assert
 (= c9128eb53_actual_token_holdings c9128eb53_actual_token_holdings))
(assert
 (= c9128eb53_fot_token_is_whitelisted c9128eb53_fot_token_is_whitelisted))
(assert
 (= c9128eb53_recorded_creator_balance_total c9128eb53_recorded_creator_balance_total))
(assert
 (= c9128eb53_transfer_received_amount c9128eb53_transfer_received_amount))
(assert
 (= c9128eb53_transfer_requested_amount c9128eb53_transfer_requested_amount))
(assert
 (= c9128eb53_users_lose_funds_occurred c9128eb53_users_lose_funds_occurred))
(define-fun report_preconditions () Bool (and c9128eb53_fot_token_is_whitelisted
     (< c9128eb53_transfer_received_amount c9128eb53_transfer_requested_amount)))
(define-fun report_safety () Bool (=> c9128eb53_fot_token_is_whitelisted
    (<= c9128eb53_recorded_creator_balance_total
        c9128eb53_actual_token_holdings)))
(define-fun report_effects () Bool (and c9128eb53_fot_token_is_whitelisted
     (not (<= c9128eb53_recorded_creator_balance_total
              c9128eb53_actual_token_holdings))
     c9128eb53_users_lose_funds_occurred))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
