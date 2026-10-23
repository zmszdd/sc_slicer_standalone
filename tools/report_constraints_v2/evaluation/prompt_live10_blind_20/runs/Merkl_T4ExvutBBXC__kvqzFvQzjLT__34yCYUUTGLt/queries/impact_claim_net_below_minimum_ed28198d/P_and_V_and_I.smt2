; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2db4d3f4_fee_deducted () Bool)
(declare-fun c2db4d3f4_gross_amount () Int)
(declare-fun c2db4d3f4_minimum_reward_threshold () Int)
(declare-fun c2db4d3f4_net_real_amount () Int)
(assert
 (= c2db4d3f4_fee_deducted c2db4d3f4_fee_deducted))
(assert
 (= c2db4d3f4_gross_amount c2db4d3f4_gross_amount))
(assert
 (= c2db4d3f4_minimum_reward_threshold c2db4d3f4_minimum_reward_threshold))
(assert
 (= c2db4d3f4_net_real_amount c2db4d3f4_net_real_amount))
(define-fun report_preconditions () Bool (and c2db4d3f4_fee_deducted
     (> c2db4d3f4_gross_amount c2db4d3f4_minimum_reward_threshold)))
(define-fun report_safety () Bool (=> (and c2db4d3f4_fee_deducted
         (> c2db4d3f4_gross_amount c2db4d3f4_minimum_reward_threshold))
    (>= c2db4d3f4_net_real_amount c2db4d3f4_minimum_reward_threshold)))
(define-fun report_effects () Bool (and c2db4d3f4_fee_deducted
     (> c2db4d3f4_gross_amount c2db4d3f4_minimum_reward_threshold)
     (not (>= c2db4d3f4_net_real_amount c2db4d3f4_minimum_reward_threshold))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
