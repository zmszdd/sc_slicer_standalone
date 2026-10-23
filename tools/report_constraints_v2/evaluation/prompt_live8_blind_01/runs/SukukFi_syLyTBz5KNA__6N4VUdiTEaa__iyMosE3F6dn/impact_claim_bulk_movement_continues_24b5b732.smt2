; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c11415d64_batch_functions_exist () Bool)
(declare-fun c11415d64_bulk_movement_continues () Bool)
(declare-fun c11415d64_contract_paused () Bool)
(declare-fun c11415d64_single_transfer_guarded () Bool)
(assert
 (= c11415d64_batch_functions_exist c11415d64_batch_functions_exist))
(assert
 (= c11415d64_bulk_movement_continues c11415d64_bulk_movement_continues))
(assert
 (= c11415d64_contract_paused c11415d64_contract_paused))
(assert
 (= c11415d64_single_transfer_guarded c11415d64_single_transfer_guarded))
(define-fun report_preconditions () Bool (and c11415d64_contract_paused
     c11415d64_batch_functions_exist
     c11415d64_single_transfer_guarded))
(define-fun report_safety () Bool (=> (and c11415d64_contract_paused
         c11415d64_batch_functions_exist
         c11415d64_single_transfer_guarded)
    (not c11415d64_bulk_movement_continues)))
(define-fun report_effects () Bool (and c11415d64_contract_paused
     c11415d64_batch_functions_exist
     c11415d64_single_transfer_guarded
     (not (not c11415d64_bulk_movement_continues))))
