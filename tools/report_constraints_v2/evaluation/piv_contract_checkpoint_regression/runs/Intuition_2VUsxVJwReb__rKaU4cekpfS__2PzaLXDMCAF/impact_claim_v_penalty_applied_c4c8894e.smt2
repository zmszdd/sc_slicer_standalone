; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c86e06db3_applied_ratio () Int)
(declare-fun c86e06db3_basis_points_divisor () Int)
(declare-fun c86e06db3_first_claim_attempted () Bool)
(declare-fun c86e06db3_raw_utilization_delta () Int)
(declare-fun c86e06db3_user_staked_trust_for_yield () Bool)
(assert
 (= c86e06db3_applied_ratio c86e06db3_applied_ratio))
(assert
 (= c86e06db3_basis_points_divisor c86e06db3_basis_points_divisor))
(assert
 (= c86e06db3_first_claim_attempted c86e06db3_first_claim_attempted))
(assert
 (= c86e06db3_raw_utilization_delta c86e06db3_raw_utilization_delta))
(assert
 (= c86e06db3_user_staked_trust_for_yield c86e06db3_user_staked_trust_for_yield))
(define-fun report_preconditions () Bool (and c86e06db3_user_staked_trust_for_yield
     c86e06db3_first_claim_attempted
     (= 0 c86e06db3_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (and c86e06db3_user_staked_trust_for_yield
         c86e06db3_first_claim_attempted
         (= 0 c86e06db3_raw_utilization_delta))
    (= c86e06db3_applied_ratio c86e06db3_basis_points_divisor)))
(define-fun report_effects () Bool (and c86e06db3_user_staked_trust_for_yield
     c86e06db3_first_claim_attempted
     (= 0 c86e06db3_raw_utilization_delta)
     (not (= c86e06db3_applied_ratio c86e06db3_basis_points_divisor))))
