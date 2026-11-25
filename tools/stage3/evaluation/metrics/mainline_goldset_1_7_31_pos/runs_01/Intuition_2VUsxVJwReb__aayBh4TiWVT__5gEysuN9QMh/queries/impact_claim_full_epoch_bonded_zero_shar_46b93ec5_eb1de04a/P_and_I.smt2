; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5d7080b4_captured_bonded_balance_nonzero () Bool)
(declare-fun c5d7080b4_lock_expires_within_epoch () Bool)
(declare-fun c5d7080b4_user_bonded_in_epoch_n () Bool)
(declare-fun c5d7080b4_user_share_percent () Int)
(assert
 (= c5d7080b4_captured_bonded_balance_nonzero c5d7080b4_captured_bonded_balance_nonzero))
(assert
 (= c5d7080b4_lock_expires_within_epoch c5d7080b4_lock_expires_within_epoch))
(assert
 (= c5d7080b4_user_bonded_in_epoch_n c5d7080b4_user_bonded_in_epoch_n))
(assert
 (= c5d7080b4_user_share_percent c5d7080b4_user_share_percent))
(define-fun report_preconditions () Bool c5d7080b4_user_bonded_in_epoch_n)
(define-fun report_safety () Bool (=> (and c5d7080b4_user_bonded_in_epoch_n c5d7080b4_lock_expires_within_epoch)
    c5d7080b4_captured_bonded_balance_nonzero))
(define-fun report_effects () Bool (and c5d7080b4_user_bonded_in_epoch_n
     c5d7080b4_lock_expires_within_epoch
     (not c5d7080b4_captured_bonded_balance_nonzero)
     (= 0 c5d7080b4_user_share_percent)
     c5d7080b4_user_bonded_in_epoch_n))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
