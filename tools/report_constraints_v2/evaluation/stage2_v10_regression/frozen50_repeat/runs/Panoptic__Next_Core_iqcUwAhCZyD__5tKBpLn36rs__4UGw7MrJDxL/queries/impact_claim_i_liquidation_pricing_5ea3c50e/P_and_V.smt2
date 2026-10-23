; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c469e9bf9_get_emas_tuple_order () Bool)
(declare-fun c469e9bf9_liquidation_pricing_correct () Bool)
(declare-fun c469e9bf9_tuple_assignment_positional () Bool)
(declare-fun c469e9bf9_twap_matches_intended () Bool)
(assert
 (= c469e9bf9_get_emas_tuple_order c469e9bf9_get_emas_tuple_order))
(assert
 (= c469e9bf9_liquidation_pricing_correct c469e9bf9_liquidation_pricing_correct))
(assert
 (= c469e9bf9_tuple_assignment_positional c469e9bf9_tuple_assignment_positional))
(assert
 (= c469e9bf9_twap_matches_intended c469e9bf9_twap_matches_intended))
(define-fun report_preconditions () Bool (and c469e9bf9_get_emas_tuple_order c469e9bf9_tuple_assignment_positional))
(define-fun report_safety () Bool (=> (and c469e9bf9_get_emas_tuple_order c469e9bf9_tuple_assignment_positional)
    (and c469e9bf9_twap_matches_intended c469e9bf9_liquidation_pricing_correct)))
(define-fun report_effects () Bool (and c469e9bf9_get_emas_tuple_order
     c469e9bf9_tuple_assignment_positional
     (not (and c469e9bf9_twap_matches_intended
               c469e9bf9_liquidation_pricing_correct))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
