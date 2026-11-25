; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cacad324a_actual_token_holdings () Int)
(declare-fun cacad324a_fot_token_is_whitelisted_reward_token () Bool)
(declare-fun cacad324a_recorded_creator_balance_total () Int)
(declare-fun cacad324a_transfer_received_amount () Int)
(declare-fun cacad324a_transfer_requested_amount () Int)
(declare-fun cacad324a_users_race_to_withdraw () Bool)
(assert
 (= cacad324a_actual_token_holdings cacad324a_actual_token_holdings))
(assert
 (= cacad324a_fot_token_is_whitelisted_reward_token cacad324a_fot_token_is_whitelisted_reward_token))
(assert
 (= cacad324a_recorded_creator_balance_total cacad324a_recorded_creator_balance_total))
(assert
 (= cacad324a_transfer_received_amount cacad324a_transfer_received_amount))
(assert
 (= cacad324a_transfer_requested_amount cacad324a_transfer_requested_amount))
(assert
 (= cacad324a_users_race_to_withdraw cacad324a_users_race_to_withdraw))
(define-fun report_preconditions () Bool (and cacad324a_fot_token_is_whitelisted_reward_token
     (< cacad324a_transfer_received_amount cacad324a_transfer_requested_amount)))
(define-fun report_safety () Bool (=> cacad324a_fot_token_is_whitelisted_reward_token
    (<= cacad324a_recorded_creator_balance_total
        cacad324a_actual_token_holdings)))
(define-fun report_effects () Bool (and cacad324a_fot_token_is_whitelisted_reward_token
     (not (<= cacad324a_recorded_creator_balance_total
              cacad324a_actual_token_holdings))
     cacad324a_users_race_to_withdraw
     cacad324a_users_race_to_withdraw))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
