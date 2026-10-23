; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce57052bf_append_requires_both_links () Bool)
(declare-fun ce57052bf_nonhead_order_exists () Bool)
(declare-fun ce57052bf_open_interest_matches_reachable () Bool)
(assert
 (= ce57052bf_append_requires_both_links ce57052bf_append_requires_both_links))
(assert
 (= ce57052bf_nonhead_order_exists ce57052bf_nonhead_order_exists))
(assert
 (= ce57052bf_open_interest_matches_reachable ce57052bf_open_interest_matches_reachable))
(define-fun report_preconditions () Bool (and ce57052bf_nonhead_order_exists ce57052bf_append_requires_both_links))
(define-fun report_safety () Bool (=> (and ce57052bf_nonhead_order_exists ce57052bf_append_requires_both_links)
    ce57052bf_open_interest_matches_reachable))
(define-fun report_effects () Bool (and ce57052bf_nonhead_order_exists
     ce57052bf_append_requires_both_links
     (not ce57052bf_open_interest_matches_reachable)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
