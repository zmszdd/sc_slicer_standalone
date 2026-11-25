; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1d38e974_net_staked () Int)
(declare-fun c1d38e974_net_staked_with_slashed () Int)
(declare-fun c1d38e974_new_users_staking_prevented () Bool)
(declare-fun c1d38e974_staking_limit () Int)
(declare-fun c1d38e974_total_slashed () Int)
(declare-fun c1d38e974_zero () Int)
(assert
 (= c1d38e974_net_staked c1d38e974_net_staked))
(assert
 (= c1d38e974_net_staked_with_slashed c1d38e974_net_staked_with_slashed))
(assert
 (= c1d38e974_new_users_staking_prevented c1d38e974_new_users_staking_prevented))
(assert
 (= c1d38e974_staking_limit c1d38e974_staking_limit))
(assert
 (= c1d38e974_total_slashed c1d38e974_total_slashed))
(assert
 (= c1d38e974_zero c1d38e974_zero))
(define-fun report_preconditions () Bool (< 0 c1d38e974_total_slashed))
(define-fun report_safety () Bool (=> (= c1d38e974_net_staked_with_slashed
       (+ c1d38e974_net_staked c1d38e974_total_slashed))
    (=> (> c1d38e974_staking_limit c1d38e974_zero)
        (= c1d38e974_net_staked
           (+ c1d38e974_net_staked c1d38e974_total_slashed)))))
(define-fun report_effects () Bool (and (= c1d38e974_net_staked_with_slashed
        (+ c1d38e974_net_staked c1d38e974_total_slashed))
     (> c1d38e974_staking_limit c1d38e974_zero)
     (not (= c1d38e974_net_staked
             (+ c1d38e974_net_staked c1d38e974_total_slashed)))
     c1d38e974_new_users_staking_prevented))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
