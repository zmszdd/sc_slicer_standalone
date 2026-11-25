; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c0d3fc53b_distributor_fee_bps () Int)
(declare-fun c0d3fc53b_spot_price_observed () Int)
(declare-fun c0d3fc53b_spot_price_with_correct_fee () Int)
(declare-fun c0d3fc53b_subsequent_swaps_affected () Bool)
(assert
 (= c0d3fc53b_distributor_fee_bps c0d3fc53b_distributor_fee_bps))
(assert
 (= c0d3fc53b_spot_price_observed c0d3fc53b_spot_price_observed))
(assert
 (= c0d3fc53b_spot_price_with_correct_fee c0d3fc53b_spot_price_with_correct_fee))
(assert
 (= c0d3fc53b_subsequent_swaps_affected c0d3fc53b_subsequent_swaps_affected))
(define-fun report_preconditions () Bool (= 5 c0d3fc53b_distributor_fee_bps))
(define-fun report_safety () Bool (=> (= 5 c0d3fc53b_distributor_fee_bps)
    (= c0d3fc53b_spot_price_observed c0d3fc53b_spot_price_with_correct_fee)))
(define-fun report_effects () Bool (and (= 5 c0d3fc53b_distributor_fee_bps)
     (not (= c0d3fc53b_spot_price_observed
             c0d3fc53b_spot_price_with_correct_fee))
     (distinct c0d3fc53b_spot_price_observed
               c0d3fc53b_spot_price_with_correct_fee)
     c0d3fc53b_subsequent_swaps_affected
     c0d3fc53b_subsequent_swaps_affected))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
