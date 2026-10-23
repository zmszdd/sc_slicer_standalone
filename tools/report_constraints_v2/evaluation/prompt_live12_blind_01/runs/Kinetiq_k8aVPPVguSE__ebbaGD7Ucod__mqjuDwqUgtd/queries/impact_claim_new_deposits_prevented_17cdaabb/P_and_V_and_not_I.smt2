; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbca715fd_new_deposit_blocked () Bool)
(declare-fun cbca715fd_real_net_staked () Int)
(declare-fun cbca715fd_staking_limit () Int)
(declare-fun cbca715fd_total_claimed () Int)
(declare-fun cbca715fd_total_rewards () Int)
(declare-fun cbca715fd_total_slashed () Int)
(declare-fun cbca715fd_total_staked () Int)
(assert
 (= cbca715fd_new_deposit_blocked cbca715fd_new_deposit_blocked))
(assert
 (= cbca715fd_real_net_staked cbca715fd_real_net_staked))
(assert
 (= cbca715fd_staking_limit cbca715fd_staking_limit))
(assert
 (= cbca715fd_total_claimed cbca715fd_total_claimed))
(assert
 (= cbca715fd_total_rewards cbca715fd_total_rewards))
(assert
 (= cbca715fd_total_slashed cbca715fd_total_slashed))
(assert
 (= cbca715fd_total_staked cbca715fd_total_staked))
(define-fun report_preconditions () Bool (and (= 500 cbca715fd_staking_limit)
     (= 400 cbca715fd_total_staked)
     (= 100 cbca715fd_total_claimed)
     (= 200 cbca715fd_total_rewards)
     (= 50 cbca715fd_total_slashed)))
(define-fun report_safety () Bool (=> (= cbca715fd_real_net_staked
       (- (+ cbca715fd_total_staked cbca715fd_total_rewards)
          (+ cbca715fd_total_claimed cbca715fd_total_slashed)))
    (=> (< cbca715fd_real_net_staked cbca715fd_staking_limit)
        (not cbca715fd_new_deposit_blocked))))
(define-fun report_effects () Bool (and (= cbca715fd_real_net_staked
        (- (+ cbca715fd_total_staked cbca715fd_total_rewards)
           (+ cbca715fd_total_claimed cbca715fd_total_slashed)))
     (< cbca715fd_real_net_staked cbca715fd_staking_limit)
     (not (not cbca715fd_new_deposit_blocked))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
