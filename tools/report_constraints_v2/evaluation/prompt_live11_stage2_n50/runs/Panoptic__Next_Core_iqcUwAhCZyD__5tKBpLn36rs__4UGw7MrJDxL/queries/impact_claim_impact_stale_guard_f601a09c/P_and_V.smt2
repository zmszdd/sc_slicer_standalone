; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc93269da_get_emas_tuple_order () Bool)
(declare-fun cc93269da_stale_guard_misclassified () Bool)
(declare-fun cc93269da_twap_tick_matches_intended () Bool)
(assert
 (= cc93269da_get_emas_tuple_order cc93269da_get_emas_tuple_order))
(assert
 (= cc93269da_stale_guard_misclassified cc93269da_stale_guard_misclassified))
(assert
 (= cc93269da_twap_tick_matches_intended cc93269da_twap_tick_matches_intended))
(define-fun report_preconditions () Bool cc93269da_get_emas_tuple_order)
(define-fun report_safety () Bool (=> cc93269da_get_emas_tuple_order
    (and cc93269da_twap_tick_matches_intended
         (not cc93269da_stale_guard_misclassified))))
(define-fun report_effects () Bool (and cc93269da_get_emas_tuple_order
     (not (and cc93269da_twap_tick_matches_intended
               (not cc93269da_stale_guard_misclassified)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
