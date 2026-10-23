; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd61f016b_dispute_amount_adjustable () Bool)
(declare-fun cd61f016b_disputer_is_set () Bool)
(declare-fun cd61f016b_merkle_updates_paused () Bool)
(assert
 (= cd61f016b_dispute_amount_adjustable cd61f016b_dispute_amount_adjustable))
(assert
 (= cd61f016b_disputer_is_set cd61f016b_disputer_is_set))
(assert
 (= cd61f016b_merkle_updates_paused cd61f016b_merkle_updates_paused))
(define-fun report_preconditions () Bool (and cd61f016b_disputer_is_set cd61f016b_merkle_updates_paused))
(define-fun report_safety () Bool (=> cd61f016b_disputer_is_set cd61f016b_dispute_amount_adjustable))
(define-fun report_effects () Bool (and cd61f016b_disputer_is_set (not cd61f016b_dispute_amount_adjustable)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
