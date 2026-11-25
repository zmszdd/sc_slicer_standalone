; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c055ad6a3_net_backing_has_surplus () Bool)
(declare-fun c055ad6a3_settle_moves_usdc_to_escrow () Bool)
(declare-fun c055ad6a3_vault_has_borrow_liability () Bool)
(assert
 (= c055ad6a3_net_backing_has_surplus c055ad6a3_net_backing_has_surplus))
(assert
 (= c055ad6a3_settle_moves_usdc_to_escrow c055ad6a3_settle_moves_usdc_to_escrow))
(assert
 (= c055ad6a3_vault_has_borrow_liability c055ad6a3_vault_has_borrow_liability))
(define-fun report_preconditions () Bool c055ad6a3_vault_has_borrow_liability)
(define-fun report_safety () Bool (=> c055ad6a3_settle_moves_usdc_to_escrow c055ad6a3_net_backing_has_surplus))
(define-fun report_effects () Bool (and c055ad6a3_settle_moves_usdc_to_escrow
     (not c055ad6a3_net_backing_has_surplus)
     c055ad6a3_settle_moves_usdc_to_escrow))
