; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c037bf77e_append_updates_both_links () Bool)
(declare-fun c037bf77e_counters_reflect_reachable () Bool)
(declare-fun c037bf77e_nonhead_order_exists () Bool)
(declare-fun c037bf77e_order_reachable () Bool)
(assert
 (= c037bf77e_append_updates_both_links c037bf77e_append_updates_both_links))
(assert
 (= c037bf77e_counters_reflect_reachable c037bf77e_counters_reflect_reachable))
(assert
 (= c037bf77e_nonhead_order_exists c037bf77e_nonhead_order_exists))
(assert
 (= c037bf77e_order_reachable c037bf77e_order_reachable))
(define-fun report_preconditions () Bool (and c037bf77e_nonhead_order_exists c037bf77e_append_updates_both_links))
(define-fun report_safety () Bool (=> (and c037bf77e_nonhead_order_exists c037bf77e_append_updates_both_links)
    (and c037bf77e_order_reachable c037bf77e_counters_reflect_reachable)))
(define-fun report_effects () Bool (and c037bf77e_nonhead_order_exists
     c037bf77e_append_updates_both_links
     (not (and c037bf77e_order_reachable c037bf77e_counters_reflect_reachable))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
