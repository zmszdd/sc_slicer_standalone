; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c10ebfe47_min_amount_ld () Int)
(declare-fun c10ebfe47_redeem_or_unstake_blocked () Bool)
(declare-fun c10ebfe47_shared_decimals () Int)
(declare-fun c10ebfe47_transfer_amount_ld () Int)
(assert
 (= c10ebfe47_min_amount_ld c10ebfe47_min_amount_ld))
(assert
 (= c10ebfe47_redeem_or_unstake_blocked c10ebfe47_redeem_or_unstake_blocked))
(assert
 (= c10ebfe47_shared_decimals c10ebfe47_shared_decimals))
(assert
 (= c10ebfe47_transfer_amount_ld c10ebfe47_transfer_amount_ld))
(define-fun report_preconditions () Bool (and (= 6 c10ebfe47_shared_decimals)
     (= c10ebfe47_min_amount_ld c10ebfe47_transfer_amount_ld)
     (distinct 0 (mod c10ebfe47_transfer_amount_ld 1000000000000))))
(define-fun report_safety () Bool (=> (and (= c10ebfe47_min_amount_ld c10ebfe47_transfer_amount_ld)
         (distinct 0 (mod c10ebfe47_transfer_amount_ld 1000000000000)))
    (not c10ebfe47_redeem_or_unstake_blocked)))
(define-fun report_effects () Bool (and (= c10ebfe47_min_amount_ld c10ebfe47_transfer_amount_ld)
     (distinct 0 (mod c10ebfe47_transfer_amount_ld 1000000000000))
     (not (not c10ebfe47_redeem_or_unstake_blocked))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
