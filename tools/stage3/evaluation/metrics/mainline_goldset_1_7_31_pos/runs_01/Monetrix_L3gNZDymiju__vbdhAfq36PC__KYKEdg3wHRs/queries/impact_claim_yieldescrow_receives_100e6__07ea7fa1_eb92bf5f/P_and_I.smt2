; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c968f5c9b_net_backing_has_no_surplus () Bool)
(declare-fun c968f5c9b_settle_moves_usdc_to_escrow () Bool)
(declare-fun c968f5c9b_vault_borrow_liability_present () Bool)
(declare-fun c968f5c9b_yieldescrow_received_usdc_amount () Int)
(assert
 (= c968f5c9b_net_backing_has_no_surplus c968f5c9b_net_backing_has_no_surplus))
(assert
 (= c968f5c9b_settle_moves_usdc_to_escrow c968f5c9b_settle_moves_usdc_to_escrow))
(assert
 (= c968f5c9b_vault_borrow_liability_present c968f5c9b_vault_borrow_liability_present))
(assert
 (= c968f5c9b_yieldescrow_received_usdc_amount c968f5c9b_yieldescrow_received_usdc_amount))
(define-fun report_preconditions () Bool c968f5c9b_vault_borrow_liability_present)
(define-fun report_safety () Bool (=> c968f5c9b_settle_moves_usdc_to_escrow
    (not c968f5c9b_net_backing_has_no_surplus)))
(define-fun report_effects () Bool (and c968f5c9b_settle_moves_usdc_to_escrow
     c968f5c9b_net_backing_has_no_surplus
     (= 100000000 c968f5c9b_yieldescrow_received_usdc_amount)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
