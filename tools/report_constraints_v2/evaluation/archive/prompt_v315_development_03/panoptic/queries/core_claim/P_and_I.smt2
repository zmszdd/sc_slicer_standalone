; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun token_supply () Int)
(declare-fun utilization_high () Bool)
(declare-fun unrealized_interest_before () Int)
(declare-fun total_assets_before () Int)
(declare-fun total_assets_after () Int)
(assert
 (= token_supply token_supply))
(assert
 (= utilization_high utilization_high))
(assert
 (= unrealized_interest_before unrealized_interest_before))
(assert
 (= total_assets_before total_assets_before))
(assert
 (= total_assets_after total_assets_after))
(define-fun report_preconditions () Bool (and (> 170141183460469231731687303715884105727 token_supply)
     utilization_high
     (= 81129638414606681695789005144063 unrealized_interest_before)))
(define-fun report_safety () Bool (=> (and (> 170141183460469231731687303715884105727 token_supply)
         utilization_high
         (= 81129638414606681695789005144063 unrealized_interest_before))
    (>= total_assets_after total_assets_before)))
(define-fun report_effects () Bool (and (> 170141183460469231731687303715884105727 token_supply)
     utilization_high
     (= 81129638414606681695789005144063 unrealized_interest_before)
     (not (>= total_assets_after total_assets_before))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
