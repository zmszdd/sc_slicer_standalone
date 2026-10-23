; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1567c4ca_dispute_token_is_fot () Bool)
(declare-fun c1567c4ca_dispute_tree_called () Bool)
(declare-fun c1567c4ca_full_amount_recorded () Bool)
(declare-fun c1567c4ca_tree_updates_blocked () Bool)
(assert
 (= c1567c4ca_dispute_token_is_fot c1567c4ca_dispute_token_is_fot))
(assert
 (= c1567c4ca_dispute_tree_called c1567c4ca_dispute_tree_called))
(assert
 (= c1567c4ca_full_amount_recorded c1567c4ca_full_amount_recorded))
(assert
 (= c1567c4ca_tree_updates_blocked c1567c4ca_tree_updates_blocked))
(define-fun report_preconditions () Bool (and c1567c4ca_dispute_token_is_fot
     c1567c4ca_dispute_tree_called
     c1567c4ca_full_amount_recorded))
(define-fun report_safety () Bool (=> (and c1567c4ca_dispute_token_is_fot
         c1567c4ca_dispute_tree_called
         c1567c4ca_full_amount_recorded)
    (not c1567c4ca_tree_updates_blocked)))
(define-fun report_effects () Bool (and c1567c4ca_dispute_token_is_fot
     c1567c4ca_dispute_tree_called
     c1567c4ca_full_amount_recorded
     (not (not c1567c4ca_tree_updates_blocked))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
