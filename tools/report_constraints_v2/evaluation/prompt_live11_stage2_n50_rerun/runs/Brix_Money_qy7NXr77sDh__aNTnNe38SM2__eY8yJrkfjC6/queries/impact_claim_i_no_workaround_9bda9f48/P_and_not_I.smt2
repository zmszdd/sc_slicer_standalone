; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c4bccc1ca_min_amount_ld_fast_redeem () Int)
(declare-fun c4bccc1ca_min_amount_ld_unstake () Int)
(declare-fun c4bccc1ca_redeem_amount () Int)
(declare-fun c4bccc1ca_shared_decimals () Int)
(declare-fun c4bccc1ca_slippage_adjustable () Bool)
(declare-fun c4bccc1ca_transfer_completes () Bool)
(assert
 (= c4bccc1ca_min_amount_ld_fast_redeem c4bccc1ca_min_amount_ld_fast_redeem))
(assert
 (= c4bccc1ca_min_amount_ld_unstake c4bccc1ca_min_amount_ld_unstake))
(assert
 (= c4bccc1ca_redeem_amount c4bccc1ca_redeem_amount))
(assert
 (= c4bccc1ca_shared_decimals c4bccc1ca_shared_decimals))
(assert
 (= c4bccc1ca_slippage_adjustable c4bccc1ca_slippage_adjustable))
(assert
 (= c4bccc1ca_transfer_completes c4bccc1ca_transfer_completes))
(define-fun report_preconditions () Bool (and (= 6 c4bccc1ca_shared_decimals)
     (= c4bccc1ca_min_amount_ld_fast_redeem c4bccc1ca_redeem_amount)
     (= c4bccc1ca_min_amount_ld_unstake c4bccc1ca_redeem_amount)
     (distinct 0 (mod c4bccc1ca_redeem_amount 1000000000000))))
(define-fun report_safety () Bool (=> (and (= c4bccc1ca_min_amount_ld_fast_redeem c4bccc1ca_redeem_amount)
         (= c4bccc1ca_min_amount_ld_unstake c4bccc1ca_redeem_amount)
         (distinct 0 (mod c4bccc1ca_redeem_amount 1000000000000)))
    (or c4bccc1ca_transfer_completes c4bccc1ca_slippage_adjustable)))
(define-fun report_effects () Bool (and (= c4bccc1ca_min_amount_ld_fast_redeem c4bccc1ca_redeem_amount)
     (= c4bccc1ca_min_amount_ld_unstake c4bccc1ca_redeem_amount)
     (distinct 0 (mod c4bccc1ca_redeem_amount 1000000000000))
     (not (or c4bccc1ca_transfer_completes c4bccc1ca_slippage_adjustable))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
