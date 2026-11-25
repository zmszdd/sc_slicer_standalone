; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun caf28ac07_distributor_fee_bps () Int)
(declare-fun caf28ac07_next_swaps_and_token_ratio_affected () Bool)
(declare-fun caf28ac07_spot_price_after_swap () Int)
(declare-fun caf28ac07_spot_price_with_correct_fee () Int)
(assert
 (= caf28ac07_distributor_fee_bps caf28ac07_distributor_fee_bps))
(assert
 (= caf28ac07_next_swaps_and_token_ratio_affected caf28ac07_next_swaps_and_token_ratio_affected))
(assert
 (= caf28ac07_spot_price_after_swap caf28ac07_spot_price_after_swap))
(assert
 (= caf28ac07_spot_price_with_correct_fee caf28ac07_spot_price_with_correct_fee))
(define-fun report_preconditions () Bool (= 5 caf28ac07_distributor_fee_bps))
(define-fun report_safety () Bool (=> (= 5 caf28ac07_distributor_fee_bps)
    (= caf28ac07_spot_price_after_swap caf28ac07_spot_price_with_correct_fee)))
(define-fun report_effects () Bool (and (= 5 caf28ac07_distributor_fee_bps)
     (not (= caf28ac07_spot_price_after_swap
             caf28ac07_spot_price_with_correct_fee))
     (distinct caf28ac07_spot_price_after_swap
               caf28ac07_spot_price_with_correct_fee)
     caf28ac07_next_swaps_and_token_ratio_affected))
