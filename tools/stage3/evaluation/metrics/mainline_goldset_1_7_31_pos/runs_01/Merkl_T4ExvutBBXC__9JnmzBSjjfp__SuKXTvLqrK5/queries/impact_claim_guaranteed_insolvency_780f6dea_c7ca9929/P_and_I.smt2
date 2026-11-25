; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8d5f6337_actual_token_holdings () Int)
(declare-fun c8d5f6337_fot_token_is_whitelisted_reward_token () Bool)
(declare-fun c8d5f6337_insolvency_observed () Bool)
(declare-fun c8d5f6337_recorded_creator_balance_total () Int)
(declare-fun c8d5f6337_transfer_delivered_amount () Int)
(declare-fun c8d5f6337_transfer_requested_amount () Int)
(assert
 (= c8d5f6337_actual_token_holdings c8d5f6337_actual_token_holdings))
(assert
 (= c8d5f6337_fot_token_is_whitelisted_reward_token c8d5f6337_fot_token_is_whitelisted_reward_token))
(assert
 (= c8d5f6337_insolvency_observed c8d5f6337_insolvency_observed))
(assert
 (= c8d5f6337_recorded_creator_balance_total c8d5f6337_recorded_creator_balance_total))
(assert
 (= c8d5f6337_transfer_delivered_amount c8d5f6337_transfer_delivered_amount))
(assert
 (= c8d5f6337_transfer_requested_amount c8d5f6337_transfer_requested_amount))
(define-fun report_preconditions () Bool (and c8d5f6337_fot_token_is_whitelisted_reward_token
     (< c8d5f6337_transfer_delivered_amount c8d5f6337_transfer_requested_amount)))
(define-fun report_safety () Bool (=> c8d5f6337_fot_token_is_whitelisted_reward_token
    (<= c8d5f6337_recorded_creator_balance_total
        c8d5f6337_actual_token_holdings)))
(define-fun report_effects () Bool (and c8d5f6337_fot_token_is_whitelisted_reward_token
     (not (<= c8d5f6337_recorded_creator_balance_total
              c8d5f6337_actual_token_holdings))
     c8d5f6337_insolvency_observed))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
