; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ce573e56b_min_amount_ld () Int)
(declare-fun ce573e56b_shared_decimals () Int)
(declare-fun ce573e56b_slippage_exceeded_revert () Bool)
(declare-fun ce573e56b_transfer_amount () Int)
(assert
 (= ce573e56b_min_amount_ld ce573e56b_min_amount_ld))
(assert
 (= ce573e56b_shared_decimals ce573e56b_shared_decimals))
(assert
 (= ce573e56b_slippage_exceeded_revert ce573e56b_slippage_exceeded_revert))
(assert
 (= ce573e56b_transfer_amount ce573e56b_transfer_amount))
(define-fun report_preconditions () Bool (and (= 6 ce573e56b_shared_decimals)
     (distinct 0 (mod ce573e56b_transfer_amount 1000000000000))
     (= ce573e56b_min_amount_ld ce573e56b_transfer_amount)))
(define-fun report_safety () Bool (=> (and (= 6 ce573e56b_shared_decimals)
         (distinct 0 (mod ce573e56b_transfer_amount 1000000000000))
         (= ce573e56b_min_amount_ld ce573e56b_transfer_amount))
    (not ce573e56b_slippage_exceeded_revert)))
(define-fun report_effects () Bool (and (= 6 ce573e56b_shared_decimals)
     (distinct 0 (mod ce573e56b_transfer_amount 1000000000000))
     (= ce573e56b_min_amount_ld ce573e56b_transfer_amount)
     (not (not ce573e56b_slippage_exceeded_revert))))
