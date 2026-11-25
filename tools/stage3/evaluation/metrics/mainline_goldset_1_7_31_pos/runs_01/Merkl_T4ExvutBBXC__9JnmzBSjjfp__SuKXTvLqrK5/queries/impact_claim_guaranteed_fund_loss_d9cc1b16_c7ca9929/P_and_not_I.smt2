; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd045ca86_actual_token_holdings () Int)
(declare-fun cd045ca86_fot_fee_deducted_on_transfer () Bool)
(declare-fun cd045ca86_fot_token_is_whitelisted () Bool)
(declare-fun cd045ca86_guaranteed_fund_loss_occurred () Bool)
(declare-fun cd045ca86_recorded_creator_balance_total () Int)
(assert
 (= cd045ca86_actual_token_holdings cd045ca86_actual_token_holdings))
(assert
 (= cd045ca86_fot_fee_deducted_on_transfer cd045ca86_fot_fee_deducted_on_transfer))
(assert
 (= cd045ca86_fot_token_is_whitelisted cd045ca86_fot_token_is_whitelisted))
(assert
 (= cd045ca86_guaranteed_fund_loss_occurred cd045ca86_guaranteed_fund_loss_occurred))
(assert
 (= cd045ca86_recorded_creator_balance_total cd045ca86_recorded_creator_balance_total))
(define-fun report_preconditions () Bool (and cd045ca86_fot_token_is_whitelisted cd045ca86_fot_fee_deducted_on_transfer))
(define-fun report_safety () Bool (=> cd045ca86_fot_token_is_whitelisted
    (<= cd045ca86_recorded_creator_balance_total
        cd045ca86_actual_token_holdings)))
(define-fun report_effects () Bool (and cd045ca86_fot_token_is_whitelisted
     (not (<= cd045ca86_recorded_creator_balance_total
              cd045ca86_actual_token_holdings))
     cd045ca86_guaranteed_fund_loss_occurred))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
