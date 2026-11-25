; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c49d6d623_captured_balance_nonzero () Bool)
(declare-fun c49d6d623_epoch_timestamp_end_n () Int)
(declare-fun c49d6d623_locked_end () Int)
(declare-fun c49d6d623_natural_expiry_locks_affected_fraction () Int)
(assert
 (= c49d6d623_captured_balance_nonzero c49d6d623_captured_balance_nonzero))
(assert
 (= c49d6d623_epoch_timestamp_end_n c49d6d623_epoch_timestamp_end_n))
(assert
 (= c49d6d623_locked_end c49d6d623_locked_end))
(assert
 (= c49d6d623_natural_expiry_locks_affected_fraction c49d6d623_natural_expiry_locks_affected_fraction))
(define-fun report_preconditions () Bool (<= c49d6d623_locked_end c49d6d623_epoch_timestamp_end_n))
(define-fun report_safety () Bool (=> (<= c49d6d623_locked_end c49d6d623_epoch_timestamp_end_n)
    c49d6d623_captured_balance_nonzero))
(define-fun report_effects () Bool (and (<= c49d6d623_locked_end c49d6d623_epoch_timestamp_end_n)
     (not c49d6d623_captured_balance_nonzero)
     (= 100 c49d6d623_natural_expiry_locks_affected_fraction)))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
