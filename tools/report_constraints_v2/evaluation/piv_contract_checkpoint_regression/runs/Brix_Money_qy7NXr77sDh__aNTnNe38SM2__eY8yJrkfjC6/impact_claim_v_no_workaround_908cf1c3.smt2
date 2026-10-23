; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb5a1f1ac_min_amount_ld () Int)
(declare-fun cb5a1f1ac_shared_decimals () Int)
(declare-fun cb5a1f1ac_slippage_adjustable () Bool)
(declare-fun cb5a1f1ac_transfer_amount_ld () Int)
(declare-fun cb5a1f1ac_transfer_succeeds () Bool)
(assert
 (= cb5a1f1ac_min_amount_ld cb5a1f1ac_min_amount_ld))
(assert
 (= cb5a1f1ac_shared_decimals cb5a1f1ac_shared_decimals))
(assert
 (= cb5a1f1ac_slippage_adjustable cb5a1f1ac_slippage_adjustable))
(assert
 (= cb5a1f1ac_transfer_amount_ld cb5a1f1ac_transfer_amount_ld))
(assert
 (= cb5a1f1ac_transfer_succeeds cb5a1f1ac_transfer_succeeds))
(define-fun report_preconditions () Bool (and (= 6 cb5a1f1ac_shared_decimals)
     (distinct 0 (mod cb5a1f1ac_transfer_amount_ld 1000000000000))
     (= cb5a1f1ac_min_amount_ld cb5a1f1ac_transfer_amount_ld)))
(define-fun report_safety () Bool (=> (and (= 6 cb5a1f1ac_shared_decimals)
         (distinct 0 (mod cb5a1f1ac_transfer_amount_ld 1000000000000))
         (= cb5a1f1ac_min_amount_ld cb5a1f1ac_transfer_amount_ld))
    (or cb5a1f1ac_transfer_succeeds cb5a1f1ac_slippage_adjustable)))
(define-fun report_effects () Bool (and (= 6 cb5a1f1ac_shared_decimals)
     (distinct 0 (mod cb5a1f1ac_transfer_amount_ld 1000000000000))
     (= cb5a1f1ac_min_amount_ld cb5a1f1ac_transfer_amount_ld)
     (not (or cb5a1f1ac_transfer_succeeds cb5a1f1ac_slippage_adjustable))))
