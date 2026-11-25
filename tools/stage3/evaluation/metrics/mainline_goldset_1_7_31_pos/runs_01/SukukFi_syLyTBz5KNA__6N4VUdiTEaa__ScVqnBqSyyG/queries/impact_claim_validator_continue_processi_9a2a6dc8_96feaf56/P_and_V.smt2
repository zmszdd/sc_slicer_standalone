; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c85d7247d_batch_transfer_executed () Bool)
(declare-fun c85d7247d_contract_is_paused () Bool)
(declare-fun c85d7247d_settlement_processed_while_paused () Bool)
(assert
 (= c85d7247d_batch_transfer_executed c85d7247d_batch_transfer_executed))
(assert
 (= c85d7247d_contract_is_paused c85d7247d_contract_is_paused))
(assert
 (= c85d7247d_settlement_processed_while_paused c85d7247d_settlement_processed_while_paused))
(define-fun report_preconditions () Bool c85d7247d_contract_is_paused)
(define-fun report_safety () Bool (=> c85d7247d_batch_transfer_executed (not c85d7247d_contract_is_paused)))
(define-fun report_effects () Bool (and c85d7247d_batch_transfer_executed
     c85d7247d_contract_is_paused
     c85d7247d_settlement_processed_while_paused
     c85d7247d_contract_is_paused))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
