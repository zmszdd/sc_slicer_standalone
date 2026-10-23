; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4bccc1ca_min_amount_ld () Int)
(declare-fun c4bccc1ca_shared_decimals () Int)
(declare-fun c4bccc1ca_slippage_user_adjustable () Bool)
(declare-fun c4bccc1ca_transfer_amount_ld () Int)
(assert
 (= c4bccc1ca_min_amount_ld c4bccc1ca_min_amount_ld))
(assert
 (= c4bccc1ca_shared_decimals c4bccc1ca_shared_decimals))
(assert
 (= c4bccc1ca_slippage_user_adjustable c4bccc1ca_slippage_user_adjustable))
(assert
 (= c4bccc1ca_transfer_amount_ld c4bccc1ca_transfer_amount_ld))
(define-fun report_preconditions () Bool (and (= 6 c4bccc1ca_shared_decimals)
     (= c4bccc1ca_min_amount_ld c4bccc1ca_transfer_amount_ld)
     (distinct 0 (mod c4bccc1ca_transfer_amount_ld 1000000000000))))
(define-fun report_safety () Bool (=> (and (= c4bccc1ca_min_amount_ld c4bccc1ca_transfer_amount_ld)
         (distinct 0 (mod c4bccc1ca_transfer_amount_ld 1000000000000)))
    c4bccc1ca_slippage_user_adjustable))
(define-fun report_effects () Bool (and (= c4bccc1ca_min_amount_ld c4bccc1ca_transfer_amount_ld)
     (distinct 0 (mod c4bccc1ca_transfer_amount_ld 1000000000000))
     (not c4bccc1ca_slippage_user_adjustable)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
