; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9886f165_actual_token_holdings () Int)
(declare-fun c9886f165_fot_token_is_whitelisted_reward_token () Bool)
(declare-fun c9886f165_fot_transfer_delivers_less_than_requested () Bool)
(declare-fun c9886f165_last_withdrawer_bears_entire_accumulated_loss () Bool)
(declare-fun c9886f165_recorded_creator_balance_total () Int)
(assert
 (= c9886f165_actual_token_holdings c9886f165_actual_token_holdings))
(assert
 (= c9886f165_fot_token_is_whitelisted_reward_token c9886f165_fot_token_is_whitelisted_reward_token))
(assert
 (= c9886f165_fot_transfer_delivers_less_than_requested c9886f165_fot_transfer_delivers_less_than_requested))
(assert
 (= c9886f165_last_withdrawer_bears_entire_accumulated_loss c9886f165_last_withdrawer_bears_entire_accumulated_loss))
(assert
 (= c9886f165_recorded_creator_balance_total c9886f165_recorded_creator_balance_total))
(define-fun report_preconditions () Bool (and c9886f165_fot_token_is_whitelisted_reward_token
     c9886f165_fot_transfer_delivers_less_than_requested))
(define-fun report_safety () Bool (=> c9886f165_fot_token_is_whitelisted_reward_token
    (<= c9886f165_recorded_creator_balance_total
        c9886f165_actual_token_holdings)))
(define-fun report_effects () Bool (and c9886f165_fot_token_is_whitelisted_reward_token
     (not (<= c9886f165_recorded_creator_balance_total
              c9886f165_actual_token_holdings))
     c9886f165_last_withdrawer_bears_entire_accumulated_loss
     c9886f165_last_withdrawer_bears_entire_accumulated_loss))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
