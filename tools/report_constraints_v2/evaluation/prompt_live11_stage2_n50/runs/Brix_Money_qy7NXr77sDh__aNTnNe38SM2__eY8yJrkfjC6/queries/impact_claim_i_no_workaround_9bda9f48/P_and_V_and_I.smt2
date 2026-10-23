; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4bccc1ca_local_decimals () Int)
(declare-fun c4bccc1ca_min_amount_ld () Int)
(declare-fun c4bccc1ca_shared_decimals () Int)
(declare-fun c4bccc1ca_slippage_manually_adjustable () Bool)
(declare-fun c4bccc1ca_transfer_amount () Int)
(declare-fun c4bccc1ca_transfer_succeeds () Bool)
(assert
 (= c4bccc1ca_local_decimals c4bccc1ca_local_decimals))
(assert
 (= c4bccc1ca_min_amount_ld c4bccc1ca_min_amount_ld))
(assert
 (= c4bccc1ca_shared_decimals c4bccc1ca_shared_decimals))
(assert
 (= c4bccc1ca_slippage_manually_adjustable c4bccc1ca_slippage_manually_adjustable))
(assert
 (= c4bccc1ca_transfer_amount c4bccc1ca_transfer_amount))
(assert
 (= c4bccc1ca_transfer_succeeds c4bccc1ca_transfer_succeeds))
(define-fun report_preconditions () Bool (and (distinct 0 (mod c4bccc1ca_transfer_amount 1000000000000))
     (= c4bccc1ca_min_amount_ld c4bccc1ca_transfer_amount)
     (= 6 c4bccc1ca_shared_decimals)
     (= 18 c4bccc1ca_local_decimals)))
(define-fun report_safety () Bool (=> (and (distinct 0 (mod c4bccc1ca_transfer_amount 1000000000000))
         (= c4bccc1ca_min_amount_ld c4bccc1ca_transfer_amount)
         (= 6 c4bccc1ca_shared_decimals)
         (= 18 c4bccc1ca_local_decimals))
    (or c4bccc1ca_transfer_succeeds c4bccc1ca_slippage_manually_adjustable)))
(define-fun report_effects () Bool (and (distinct 0 (mod c4bccc1ca_transfer_amount 1000000000000))
     (= c4bccc1ca_min_amount_ld c4bccc1ca_transfer_amount)
     (= 6 c4bccc1ca_shared_decimals)
     (= 18 c4bccc1ca_local_decimals)
     (not (or c4bccc1ca_transfer_succeeds
              c4bccc1ca_slippage_manually_adjustable))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
