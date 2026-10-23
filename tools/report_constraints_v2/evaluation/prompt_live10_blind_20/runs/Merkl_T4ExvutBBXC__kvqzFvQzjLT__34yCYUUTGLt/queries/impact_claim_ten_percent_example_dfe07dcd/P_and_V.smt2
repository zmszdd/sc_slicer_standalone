; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1f82d8c7_fee_deducted () Bool)
(declare-fun c1f82d8c7_gross_amount () Int)
(declare-fun c1f82d8c7_minimum_reward_threshold () Int)
(declare-fun c1f82d8c7_net_real_amount () Int)
(assert
 (= c1f82d8c7_fee_deducted c1f82d8c7_fee_deducted))
(assert
 (= c1f82d8c7_gross_amount c1f82d8c7_gross_amount))
(assert
 (= c1f82d8c7_minimum_reward_threshold c1f82d8c7_minimum_reward_threshold))
(assert
 (= c1f82d8c7_net_real_amount c1f82d8c7_net_real_amount))
(define-fun report_preconditions () Bool (and c1f82d8c7_fee_deducted
     (> c1f82d8c7_gross_amount c1f82d8c7_minimum_reward_threshold)))
(define-fun report_safety () Bool (=> (and c1f82d8c7_fee_deducted
         (> c1f82d8c7_gross_amount c1f82d8c7_minimum_reward_threshold))
    (>= c1f82d8c7_net_real_amount c1f82d8c7_minimum_reward_threshold)))
(define-fun report_effects () Bool (and c1f82d8c7_fee_deducted
     (> c1f82d8c7_gross_amount c1f82d8c7_minimum_reward_threshold)
     (not (>= c1f82d8c7_net_real_amount c1f82d8c7_minimum_reward_threshold))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
