; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c184802e5_basis_points_divisor () Int)
(declare-fun c184802e5_is_first_claim () Bool)
(declare-fun c184802e5_raw_utilization_delta () Int)
(declare-fun c184802e5_returned_ratio () Int)
(declare-fun c184802e5_stakes_trust_passively () Bool)
(assert
 (= c184802e5_basis_points_divisor c184802e5_basis_points_divisor))
(assert
 (= c184802e5_is_first_claim c184802e5_is_first_claim))
(assert
 (= c184802e5_raw_utilization_delta c184802e5_raw_utilization_delta))
(assert
 (= c184802e5_returned_ratio c184802e5_returned_ratio))
(assert
 (= c184802e5_stakes_trust_passively c184802e5_stakes_trust_passively))
(define-fun report_preconditions () Bool (and c184802e5_stakes_trust_passively
     c184802e5_is_first_claim
     (= 0 c184802e5_raw_utilization_delta)))
(define-fun report_safety () Bool (=> (and c184802e5_is_first_claim (= 0 c184802e5_raw_utilization_delta))
    (= c184802e5_returned_ratio c184802e5_basis_points_divisor)))
(define-fun report_effects () Bool (and c184802e5_is_first_claim
     (= 0 c184802e5_raw_utilization_delta)
     (not (= c184802e5_returned_ratio c184802e5_basis_points_divisor))))
(assert report_preconditions)
(check-sat)
(get-model)
