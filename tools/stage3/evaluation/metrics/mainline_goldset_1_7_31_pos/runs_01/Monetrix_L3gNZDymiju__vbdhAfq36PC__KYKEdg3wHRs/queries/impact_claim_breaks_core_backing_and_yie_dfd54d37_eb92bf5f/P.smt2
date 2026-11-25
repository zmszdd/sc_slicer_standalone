; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ccfbbab47_backing_and_yield_settlement_invariants_broken () Bool)
(declare-fun ccfbbab47_net_backing_has_no_surplus () Bool)
(declare-fun ccfbbab47_settle_moves_usdc_to_escrow () Bool)
(declare-fun ccfbbab47_vault_borrow_liability_present () Bool)
(assert
 (= ccfbbab47_backing_and_yield_settlement_invariants_broken ccfbbab47_backing_and_yield_settlement_invariants_broken))
(assert
 (= ccfbbab47_net_backing_has_no_surplus ccfbbab47_net_backing_has_no_surplus))
(assert
 (= ccfbbab47_settle_moves_usdc_to_escrow ccfbbab47_settle_moves_usdc_to_escrow))
(assert
 (= ccfbbab47_vault_borrow_liability_present ccfbbab47_vault_borrow_liability_present))
(define-fun report_preconditions () Bool ccfbbab47_vault_borrow_liability_present)
(define-fun report_safety () Bool (=> ccfbbab47_settle_moves_usdc_to_escrow
    (not ccfbbab47_net_backing_has_no_surplus)))
(define-fun report_effects () Bool (and ccfbbab47_settle_moves_usdc_to_escrow
     ccfbbab47_net_backing_has_no_surplus
     ccfbbab47_backing_and_yield_settlement_invariants_broken
     ccfbbab47_settle_moves_usdc_to_escrow))
(assert report_preconditions)
(check-sat)
(get-model)
