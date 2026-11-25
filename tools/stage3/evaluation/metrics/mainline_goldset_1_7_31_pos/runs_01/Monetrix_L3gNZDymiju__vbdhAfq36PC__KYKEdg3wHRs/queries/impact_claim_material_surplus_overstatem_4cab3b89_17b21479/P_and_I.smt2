; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7e9eaa9d_backing_accounts_for_borrow_liability () Bool)
(declare-fun c7e9eaa9d_backing_uses_borrow_lend_supply () Bool)
(declare-fun c7e9eaa9d_borrow_liability_present () Bool)
(declare-fun c7e9eaa9d_surplus_overstated () Bool)
(assert
 (= c7e9eaa9d_backing_accounts_for_borrow_liability c7e9eaa9d_backing_accounts_for_borrow_liability))
(assert
 (= c7e9eaa9d_backing_uses_borrow_lend_supply c7e9eaa9d_backing_uses_borrow_lend_supply))
(assert
 (= c7e9eaa9d_borrow_liability_present c7e9eaa9d_borrow_liability_present))
(assert
 (= c7e9eaa9d_surplus_overstated c7e9eaa9d_surplus_overstated))
(define-fun report_preconditions () Bool (and c7e9eaa9d_borrow_liability_present
     c7e9eaa9d_backing_uses_borrow_lend_supply))
(define-fun report_safety () Bool c7e9eaa9d_backing_accounts_for_borrow_liability)
(define-fun report_effects () Bool (and c7e9eaa9d_backing_uses_borrow_lend_supply
     (not c7e9eaa9d_backing_accounts_for_borrow_liability)
     c7e9eaa9d_surplus_overstated))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
