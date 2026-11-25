; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbda5e641_actual_amount_under_management () Int)
(declare-fun cbda5e641_net_staked_used_in_check () Int)
(declare-fun cbda5e641_new_stake_rejected () Bool)
(declare-fun cbda5e641_staking_limit () Int)
(declare-fun cbda5e641_total_slashed_amount () Int)
(assert
 (= cbda5e641_actual_amount_under_management cbda5e641_actual_amount_under_management))
(assert
 (= cbda5e641_net_staked_used_in_check cbda5e641_net_staked_used_in_check))
(assert
 (= cbda5e641_new_stake_rejected cbda5e641_new_stake_rejected))
(assert
 (= cbda5e641_staking_limit cbda5e641_staking_limit))
(assert
 (= cbda5e641_total_slashed_amount cbda5e641_total_slashed_amount))
(define-fun report_preconditions () Bool (and (<= 0 cbda5e641_staking_limit) (< 0 cbda5e641_total_slashed_amount)))
(define-fun report_safety () Bool (=> (= cbda5e641_actual_amount_under_management
       (- cbda5e641_net_staked_used_in_check cbda5e641_total_slashed_amount))
    (=> (< cbda5e641_actual_amount_under_management cbda5e641_staking_limit)
        (not cbda5e641_new_stake_rejected))))
(define-fun report_effects () Bool (and (= cbda5e641_actual_amount_under_management
        (- cbda5e641_net_staked_used_in_check cbda5e641_total_slashed_amount))
     (and (< cbda5e641_actual_amount_under_management cbda5e641_staking_limit)
          cbda5e641_new_stake_rejected)
     cbda5e641_new_stake_rejected
     (and (< cbda5e641_actual_amount_under_management cbda5e641_staking_limit)
          cbda5e641_new_stake_rejected)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
