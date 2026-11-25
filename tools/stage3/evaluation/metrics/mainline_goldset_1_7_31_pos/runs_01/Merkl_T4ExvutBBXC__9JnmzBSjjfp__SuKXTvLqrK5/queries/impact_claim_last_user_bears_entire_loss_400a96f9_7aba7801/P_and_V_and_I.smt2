; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5476d6e3_actual_received_amount () Int)
(declare-fun c5476d6e3_credited_balance_amount () Int)
(declare-fun c5476d6e3_fot_token_is_whitelisted () Bool)
(declare-fun c5476d6e3_last_withdrawer_bears_entire_loss () Bool)
(declare-fun c5476d6e3_transfer_received_amount () Int)
(declare-fun c5476d6e3_transfer_requested_amount () Int)
(assert
 (= c5476d6e3_actual_received_amount c5476d6e3_actual_received_amount))
(assert
 (= c5476d6e3_credited_balance_amount c5476d6e3_credited_balance_amount))
(assert
 (= c5476d6e3_fot_token_is_whitelisted c5476d6e3_fot_token_is_whitelisted))
(assert
 (= c5476d6e3_last_withdrawer_bears_entire_loss c5476d6e3_last_withdrawer_bears_entire_loss))
(assert
 (= c5476d6e3_transfer_received_amount c5476d6e3_transfer_received_amount))
(assert
 (= c5476d6e3_transfer_requested_amount c5476d6e3_transfer_requested_amount))
(define-fun report_preconditions () Bool (and c5476d6e3_fot_token_is_whitelisted
     (< c5476d6e3_transfer_received_amount c5476d6e3_transfer_requested_amount)))
(define-fun report_safety () Bool (=> c5476d6e3_fot_token_is_whitelisted
    (= c5476d6e3_credited_balance_amount c5476d6e3_actual_received_amount)))
(define-fun report_effects () Bool (and c5476d6e3_fot_token_is_whitelisted
     (not (= c5476d6e3_credited_balance_amount c5476d6e3_actual_received_amount))
     c5476d6e3_last_withdrawer_bears_entire_loss
     c5476d6e3_last_withdrawer_bears_entire_loss))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
