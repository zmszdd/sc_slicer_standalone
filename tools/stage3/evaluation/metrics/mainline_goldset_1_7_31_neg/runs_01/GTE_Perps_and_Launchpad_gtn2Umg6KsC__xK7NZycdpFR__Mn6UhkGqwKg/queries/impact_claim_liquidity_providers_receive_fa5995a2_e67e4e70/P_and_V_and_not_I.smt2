; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c73f41b6c_distributor_fee_bps () Int)
(declare-fun c73f41b6c_lp_fees_expected () Int)
(declare-fun c73f41b6c_lp_fees_received () Int)
(declare-fun c73f41b6c_swap_fee_distribution_applies () Bool)
(assert
 (= c73f41b6c_distributor_fee_bps c73f41b6c_distributor_fee_bps))
(assert
 (= c73f41b6c_lp_fees_expected c73f41b6c_lp_fees_expected))
(assert
 (= c73f41b6c_lp_fees_received c73f41b6c_lp_fees_received))
(assert
 (= c73f41b6c_swap_fee_distribution_applies c73f41b6c_swap_fee_distribution_applies))
(define-fun report_preconditions () Bool (and (= 5 c73f41b6c_distributor_fee_bps)
     c73f41b6c_swap_fee_distribution_applies))
(define-fun report_safety () Bool (>= c73f41b6c_lp_fees_received c73f41b6c_lp_fees_expected))
(define-fun report_effects () Bool (and c73f41b6c_swap_fee_distribution_applies
     (not (>= c73f41b6c_lp_fees_received c73f41b6c_lp_fees_expected))
     (< c73f41b6c_lp_fees_received c73f41b6c_lp_fees_expected)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
