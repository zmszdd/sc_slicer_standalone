; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cf7ea242f_non_head_order_present () Bool)
(declare-fun cf7ea242f_open_interest_counter () Int)
(declare-fun cf7ea242f_order_appended () Bool)
(declare-fun cf7ea242f_reachable_order_count () Int)
(assert
 (= cf7ea242f_non_head_order_present cf7ea242f_non_head_order_present))
(assert
 (= cf7ea242f_open_interest_counter cf7ea242f_open_interest_counter))
(assert
 (= cf7ea242f_order_appended cf7ea242f_order_appended))
(assert
 (= cf7ea242f_reachable_order_count cf7ea242f_reachable_order_count))
(define-fun report_preconditions () Bool (and cf7ea242f_order_appended cf7ea242f_non_head_order_present))
(define-fun report_safety () Bool (=> (and cf7ea242f_order_appended cf7ea242f_non_head_order_present)
    (= cf7ea242f_open_interest_counter cf7ea242f_reachable_order_count)))
(define-fun report_effects () Bool (and cf7ea242f_order_appended
     cf7ea242f_non_head_order_present
     (not (= cf7ea242f_open_interest_counter cf7ea242f_reachable_order_count))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
