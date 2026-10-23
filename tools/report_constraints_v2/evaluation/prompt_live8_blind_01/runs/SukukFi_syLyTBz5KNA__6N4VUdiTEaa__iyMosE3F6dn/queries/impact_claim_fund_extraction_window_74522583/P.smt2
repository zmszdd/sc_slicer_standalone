; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8ff375d6_batch_functions_exist () Bool)
(declare-fun c8ff375d6_batch_transfer_executed () Bool)
(declare-fun c8ff375d6_contract_paused () Bool)
(declare-fun c8ff375d6_single_transfer_guarded () Bool)
(assert
 (= c8ff375d6_batch_functions_exist c8ff375d6_batch_functions_exist))
(assert
 (= c8ff375d6_batch_transfer_executed c8ff375d6_batch_transfer_executed))
(assert
 (= c8ff375d6_contract_paused c8ff375d6_contract_paused))
(assert
 (= c8ff375d6_single_transfer_guarded c8ff375d6_single_transfer_guarded))
(define-fun report_preconditions () Bool (and c8ff375d6_contract_paused
     c8ff375d6_batch_functions_exist
     c8ff375d6_single_transfer_guarded))
(define-fun report_safety () Bool (=> (and c8ff375d6_contract_paused
         c8ff375d6_batch_functions_exist
         c8ff375d6_single_transfer_guarded)
    (not c8ff375d6_batch_transfer_executed)))
(define-fun report_effects () Bool (and c8ff375d6_contract_paused
     c8ff375d6_batch_functions_exist
     c8ff375d6_single_transfer_guarded
     (not (not c8ff375d6_batch_transfer_executed))))
(assert report_preconditions)
(check-sat)
(get-model)
