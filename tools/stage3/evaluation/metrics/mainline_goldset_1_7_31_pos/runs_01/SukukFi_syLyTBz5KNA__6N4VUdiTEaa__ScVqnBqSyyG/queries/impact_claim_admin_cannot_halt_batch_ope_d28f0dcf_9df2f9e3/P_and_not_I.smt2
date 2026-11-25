; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c99d0a5a5_batch_operations_execute_while_paused () Bool)
(declare-fun c99d0a5a5_batch_operations_halted () Bool)
(declare-fun c99d0a5a5_contract_paused () Bool)
(assert
 (= c99d0a5a5_batch_operations_execute_while_paused c99d0a5a5_batch_operations_execute_while_paused))
(assert
 (= c99d0a5a5_batch_operations_halted c99d0a5a5_batch_operations_halted))
(assert
 (= c99d0a5a5_contract_paused c99d0a5a5_contract_paused))
(define-fun report_preconditions () Bool c99d0a5a5_contract_paused)
(define-fun report_safety () Bool (=> c99d0a5a5_contract_paused c99d0a5a5_batch_operations_halted))
(define-fun report_effects () Bool (and c99d0a5a5_contract_paused
     (not c99d0a5a5_batch_operations_halted)
     c99d0a5a5_batch_operations_execute_while_paused
     c99d0a5a5_contract_paused))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
