; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun paid_fee () Int)
(declare-fun quoted_fee () Int)
(declare-fun fee_mismatch_reverted () Bool)
(declare-fun message_dispatched () Bool)
(assert
 (= paid_fee paid_fee))
(assert
 (= quoted_fee quoted_fee))
(assert
 (= fee_mismatch_reverted fee_mismatch_reverted))
(assert
 (= message_dispatched message_dispatched))
(define-fun report_preconditions () Bool (and (> paid_fee quoted_fee) (<= 0 quoted_fee)))
(define-fun report_safety () Bool (=> (>= paid_fee quoted_fee) (not fee_mismatch_reverted)))
(define-fun report_effects () Bool (and fee_mismatch_reverted (not message_dispatched)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
