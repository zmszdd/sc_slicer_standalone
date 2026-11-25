; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c66fb11c7_actual_received_amount () Int)
(declare-fun c66fb11c7_bank_run_race_occurs () Bool)
(declare-fun c66fb11c7_credited_balance_amount () Int)
(declare-fun c66fb11c7_fot_token_is_whitelisted () Bool)
(declare-fun c66fb11c7_received_transfer_amount () Int)
(declare-fun c66fb11c7_requested_transfer_amount () Int)
(assert
 (= c66fb11c7_actual_received_amount c66fb11c7_actual_received_amount))
(assert
 (= c66fb11c7_bank_run_race_occurs c66fb11c7_bank_run_race_occurs))
(assert
 (= c66fb11c7_credited_balance_amount c66fb11c7_credited_balance_amount))
(assert
 (= c66fb11c7_fot_token_is_whitelisted c66fb11c7_fot_token_is_whitelisted))
(assert
 (= c66fb11c7_received_transfer_amount c66fb11c7_received_transfer_amount))
(assert
 (= c66fb11c7_requested_transfer_amount c66fb11c7_requested_transfer_amount))
(define-fun report_preconditions () Bool (and c66fb11c7_fot_token_is_whitelisted
     (< c66fb11c7_received_transfer_amount c66fb11c7_requested_transfer_amount)))
(define-fun report_safety () Bool (=> c66fb11c7_fot_token_is_whitelisted
    (= c66fb11c7_credited_balance_amount c66fb11c7_actual_received_amount)))
(define-fun report_effects () Bool (and c66fb11c7_fot_token_is_whitelisted
     (not (= c66fb11c7_credited_balance_amount c66fb11c7_actual_received_amount))
     c66fb11c7_bank_run_race_occurs
     c66fb11c7_bank_run_race_occurs))
(assert report_preconditions)
(check-sat)
(get-model)
