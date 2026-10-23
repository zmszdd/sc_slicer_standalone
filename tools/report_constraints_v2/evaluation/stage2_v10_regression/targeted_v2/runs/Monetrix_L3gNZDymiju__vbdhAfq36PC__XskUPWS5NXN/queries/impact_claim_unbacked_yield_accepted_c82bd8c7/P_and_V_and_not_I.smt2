; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cadd152bd_auto_borrow_occurred () Bool)
(declare-fun cadd152bd_portfolio_margin_active () Bool)
(declare-fun cadd152bd_proposed_yield () Int)
(declare-fun cadd152bd_real_surplus () Int)
(declare-fun cadd152bd_settle_accepted_unbacked_yield () Bool)
(assert
 (= cadd152bd_auto_borrow_occurred cadd152bd_auto_borrow_occurred))
(assert
 (= cadd152bd_portfolio_margin_active cadd152bd_portfolio_margin_active))
(assert
 (= cadd152bd_proposed_yield cadd152bd_proposed_yield))
(assert
 (= cadd152bd_real_surplus cadd152bd_real_surplus))
(assert
 (= cadd152bd_settle_accepted_unbacked_yield cadd152bd_settle_accepted_unbacked_yield))
(define-fun report_preconditions () Bool (and cadd152bd_portfolio_margin_active cadd152bd_auto_borrow_occurred))
(define-fun report_safety () Bool (=> (and cadd152bd_portfolio_margin_active cadd152bd_auto_borrow_occurred)
    (or (<= cadd152bd_proposed_yield cadd152bd_real_surplus)
        (not cadd152bd_settle_accepted_unbacked_yield))))
(define-fun report_effects () Bool (and cadd152bd_portfolio_margin_active
     cadd152bd_auto_borrow_occurred
     (not (or (<= cadd152bd_proposed_yield cadd152bd_real_surplus)
              (not cadd152bd_settle_accepted_unbacked_yield)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
