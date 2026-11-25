; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c209f042d_bonded_balance_at_epoch_end () Int)
(declare-fun c209f042d_bonded_balance_before_expiry () Int)
(declare-fun c209f042d_epoch_timestamp_end_n () Int)
(declare-fun c209f042d_lock_end () Int)
(declare-fun c209f042d_user_bonded_during_epoch_n () Bool)
(declare-fun c209f042d_zero_balance () Int)
(assert
 (= c209f042d_bonded_balance_at_epoch_end c209f042d_bonded_balance_at_epoch_end))
(assert
 (= c209f042d_bonded_balance_before_expiry c209f042d_bonded_balance_before_expiry))
(assert
 (= c209f042d_epoch_timestamp_end_n c209f042d_epoch_timestamp_end_n))
(assert
 (= c209f042d_lock_end c209f042d_lock_end))
(assert
 (= c209f042d_user_bonded_during_epoch_n c209f042d_user_bonded_during_epoch_n))
(assert
 (= c209f042d_zero_balance c209f042d_zero_balance))
(define-fun report_preconditions () Bool (and (<= c209f042d_lock_end c209f042d_epoch_timestamp_end_n)
     c209f042d_user_bonded_during_epoch_n))
(define-fun report_safety () Bool (=> (and (<= c209f042d_lock_end c209f042d_epoch_timestamp_end_n)
         c209f042d_user_bonded_during_epoch_n)
    (> c209f042d_bonded_balance_before_expiry c209f042d_zero_balance)))
(define-fun report_effects () Bool (and (<= c209f042d_lock_end c209f042d_epoch_timestamp_end_n)
     c209f042d_user_bonded_during_epoch_n
     (not (> c209f042d_bonded_balance_before_expiry c209f042d_zero_balance))
     c209f042d_user_bonded_during_epoch_n
     (= c209f042d_bonded_balance_at_epoch_end c209f042d_zero_balance)
     c209f042d_user_bonded_during_epoch_n))
(assert report_preconditions)
(check-sat)
(get-model)
