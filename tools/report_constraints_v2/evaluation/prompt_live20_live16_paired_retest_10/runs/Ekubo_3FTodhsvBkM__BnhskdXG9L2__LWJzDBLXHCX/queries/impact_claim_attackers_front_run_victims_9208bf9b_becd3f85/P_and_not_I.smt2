; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c90da0bec_attacker_front_runs_to_limit () Bool)
(declare-fun c90da0bec_attacker_observes_limit () Bool)
(declare-fun c90da0bec_noop_swap_with_value_accepted () Bool)
(declare-fun c90da0bec_pool_sqrt_ratio_at_victim_exec () Int)
(declare-fun c90da0bec_victim_msg_value () Int)
(declare-fun c90da0bec_victim_sqrt_ratio_limit () Int)
(assert
 (= c90da0bec_attacker_front_runs_to_limit c90da0bec_attacker_front_runs_to_limit))
(assert
 (= c90da0bec_attacker_observes_limit c90da0bec_attacker_observes_limit))
(assert
 (= c90da0bec_noop_swap_with_value_accepted c90da0bec_noop_swap_with_value_accepted))
(assert
 (= c90da0bec_pool_sqrt_ratio_at_victim_exec c90da0bec_pool_sqrt_ratio_at_victim_exec))
(assert
 (= c90da0bec_victim_msg_value c90da0bec_victim_msg_value))
(assert
 (= c90da0bec_victim_sqrt_ratio_limit c90da0bec_victim_sqrt_ratio_limit))
(define-fun report_preconditions () Bool (and (= 10 c90da0bec_victim_msg_value)
     c90da0bec_attacker_observes_limit
     c90da0bec_attacker_front_runs_to_limit))
(define-fun report_safety () Bool (=> (and (= c90da0bec_pool_sqrt_ratio_at_victim_exec
            c90da0bec_victim_sqrt_ratio_limit)
         (< 0 c90da0bec_victim_msg_value))
    (not c90da0bec_noop_swap_with_value_accepted)))
(define-fun report_effects () Bool (and (= c90da0bec_pool_sqrt_ratio_at_victim_exec
        c90da0bec_victim_sqrt_ratio_limit)
     c90da0bec_noop_swap_with_value_accepted))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
