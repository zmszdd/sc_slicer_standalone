; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8425e834_dispute_token_is_fot () Bool)
(declare-fun c8425e834_dispute_tree_called () Bool)
(declare-fun c8425e834_recorded_dispute_amount () Int)
(declare-fun c8425e834_resolve_dispute_completed () Bool)
(assert
 (= c8425e834_dispute_token_is_fot c8425e834_dispute_token_is_fot))
(assert
 (= c8425e834_dispute_tree_called c8425e834_dispute_tree_called))
(assert
 (= c8425e834_recorded_dispute_amount c8425e834_recorded_dispute_amount))
(assert
 (= c8425e834_resolve_dispute_completed c8425e834_resolve_dispute_completed))
(define-fun report_preconditions () Bool (and c8425e834_dispute_token_is_fot
     c8425e834_dispute_tree_called
     (< 0 c8425e834_recorded_dispute_amount)))
(define-fun report_safety () Bool (=> (and c8425e834_dispute_token_is_fot
         c8425e834_dispute_tree_called
         (< 0 c8425e834_recorded_dispute_amount))
    c8425e834_resolve_dispute_completed))
(define-fun report_effects () Bool (and c8425e834_dispute_token_is_fot
     c8425e834_dispute_tree_called
     (< 0 c8425e834_recorded_dispute_amount)
     (not c8425e834_resolve_dispute_completed)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
