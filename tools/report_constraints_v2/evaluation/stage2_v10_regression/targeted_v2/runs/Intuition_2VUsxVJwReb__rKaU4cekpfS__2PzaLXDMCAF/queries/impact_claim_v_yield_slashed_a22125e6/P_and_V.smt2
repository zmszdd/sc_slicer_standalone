; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce8eb57f3_applied_lower_bound () Int)
(declare-fun ce8eb57f3_basis_points_divisor () Int)
(declare-fun ce8eb57f3_is_first_claim () Bool)
(declare-fun ce8eb57f3_is_new_passive_user () Bool)
(declare-fun ce8eb57f3_raw_utilization_delta () Int)
(assert
 (= ce8eb57f3_applied_lower_bound ce8eb57f3_applied_lower_bound))
(assert
 (= ce8eb57f3_basis_points_divisor ce8eb57f3_basis_points_divisor))
(assert
 (= ce8eb57f3_is_first_claim ce8eb57f3_is_first_claim))
(assert
 (= ce8eb57f3_is_new_passive_user ce8eb57f3_is_new_passive_user))
(assert
 (= ce8eb57f3_raw_utilization_delta ce8eb57f3_raw_utilization_delta))
(define-fun report_preconditions () Bool (and ce8eb57f3_is_new_passive_user
     ce8eb57f3_is_first_claim
     (= 0 ce8eb57f3_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (and ce8eb57f3_is_new_passive_user
         ce8eb57f3_is_first_claim
         (= 0 ce8eb57f3_raw_utilization_delta))
    (= ce8eb57f3_applied_lower_bound ce8eb57f3_basis_points_divisor)))
(define-fun report_effects () Bool (and ce8eb57f3_is_new_passive_user
     ce8eb57f3_is_first_claim
     (= 0 ce8eb57f3_raw_utilization_delta)
     (not (= ce8eb57f3_applied_lower_bound ce8eb57f3_basis_points_divisor))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
