; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun fok_order_placed () Bool)
(declare-fun only_dust_remainder () Bool)
(declare-fun order_otherwise_fillable () Bool)
(declare-fun order_reverts () Bool)
(assert
 (= fok_order_placed fok_order_placed))
(assert
 (= only_dust_remainder only_dust_remainder))
(assert
 (= order_otherwise_fillable order_otherwise_fillable))
(assert
 (= order_reverts order_reverts))
(define-fun report_preconditions () Bool (and fok_order_placed only_dust_remainder order_otherwise_fillable))
(define-fun report_safety () Bool (=> only_dust_remainder (not order_reverts)))
(define-fun report_effects () Bool (and only_dust_remainder order_reverts))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
