; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c1cb0bc5b_backing_accounts_for_borrow_liabilities () Bool)
(declare-fun c1cb0bc5b_backing_uses_borrow_lend_supply () Bool)
(declare-fun c1cb0bc5b_borrow_value_present () Bool)
(declare-fun c1cb0bc5b_core_backing_and_yield_settlement_invariants_broken () Bool)
(assert
 (= c1cb0bc5b_backing_accounts_for_borrow_liabilities c1cb0bc5b_backing_accounts_for_borrow_liabilities))
(assert
 (= c1cb0bc5b_backing_uses_borrow_lend_supply c1cb0bc5b_backing_uses_borrow_lend_supply))
(assert
 (= c1cb0bc5b_borrow_value_present c1cb0bc5b_borrow_value_present))
(assert
 (= c1cb0bc5b_core_backing_and_yield_settlement_invariants_broken c1cb0bc5b_core_backing_and_yield_settlement_invariants_broken))
(define-fun report_preconditions () Bool (and c1cb0bc5b_borrow_value_present c1cb0bc5b_backing_uses_borrow_lend_supply))
(define-fun report_safety () Bool c1cb0bc5b_backing_accounts_for_borrow_liabilities)
(define-fun report_effects () Bool (and c1cb0bc5b_backing_uses_borrow_lend_supply
     (not c1cb0bc5b_backing_accounts_for_borrow_liabilities)
     c1cb0bc5b_core_backing_and_yield_settlement_invariants_broken))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
