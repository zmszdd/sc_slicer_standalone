; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbd582769_actual_tokens_under_management () Int)
(declare-fun cbd582769_net_staked_used_in_check () Int)
(declare-fun cbd582769_new_stake_rejected () Bool)
(declare-fun cbd582769_staking_limit () Int)
(declare-fun cbd582769_total_slashed_amount () Int)
(assert
 (= cbd582769_actual_tokens_under_management cbd582769_actual_tokens_under_management))
(assert
 (= cbd582769_net_staked_used_in_check cbd582769_net_staked_used_in_check))
(assert
 (= cbd582769_new_stake_rejected cbd582769_new_stake_rejected))
(assert
 (= cbd582769_staking_limit cbd582769_staking_limit))
(assert
 (= cbd582769_total_slashed_amount cbd582769_total_slashed_amount))
(define-fun report_preconditions () Bool (and (<= 0 cbd582769_staking_limit)
     (< 0 cbd582769_total_slashed_amount)
     cbd582769_new_stake_rejected))
(define-fun report_safety () Bool (=> (= cbd582769_actual_tokens_under_management
       (- cbd582769_net_staked_used_in_check cbd582769_total_slashed_amount))
    (= cbd582769_net_staked_used_in_check
       cbd582769_actual_tokens_under_management)))
(define-fun report_effects () Bool (and (= cbd582769_actual_tokens_under_management
        (- cbd582769_net_staked_used_in_check cbd582769_total_slashed_amount))
     cbd582769_new_stake_rejected
     (not (= cbd582769_net_staked_used_in_check
             cbd582769_actual_tokens_under_management))
     cbd582769_new_stake_rejected))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
