; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9de92957_net_backing_has_no_surplus () Bool)
(declare-fun c9de92957_settle_moves_usdc_to_escrow () Bool)
(declare-fun c9de92957_vault_borrow_liability_present () Bool)
(assert
 (= c9de92957_net_backing_has_no_surplus c9de92957_net_backing_has_no_surplus))
(assert
 (= c9de92957_settle_moves_usdc_to_escrow c9de92957_settle_moves_usdc_to_escrow))
(assert
 (= c9de92957_vault_borrow_liability_present c9de92957_vault_borrow_liability_present))
(define-fun report_preconditions () Bool c9de92957_vault_borrow_liability_present)
(define-fun report_safety () Bool (=> c9de92957_settle_moves_usdc_to_escrow
    (not c9de92957_net_backing_has_no_surplus)))
(define-fun report_effects () Bool (and c9de92957_settle_moves_usdc_to_escrow
     c9de92957_net_backing_has_no_surplus
     c9de92957_settle_moves_usdc_to_escrow))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
