; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c39c1f7a5_credited_amount () Int)
(declare-fun c39c1f7a5_deposit_amount () Int)
(declare-fun c39c1f7a5_is_fee_on_transfer_token () Bool)
(declare-fun c39c1f7a5_received_amount () Int)
(declare-fun c39c1f7a5_recorded_balance_exceeds_holdings () Bool)
(assert
 (= c39c1f7a5_credited_amount c39c1f7a5_credited_amount))
(assert
 (= c39c1f7a5_deposit_amount c39c1f7a5_deposit_amount))
(assert
 (= c39c1f7a5_is_fee_on_transfer_token c39c1f7a5_is_fee_on_transfer_token))
(assert
 (= c39c1f7a5_received_amount c39c1f7a5_received_amount))
(assert
 (= c39c1f7a5_recorded_balance_exceeds_holdings c39c1f7a5_recorded_balance_exceeds_holdings))
(define-fun report_preconditions () Bool (and c39c1f7a5_is_fee_on_transfer_token
     (= 10000 c39c1f7a5_deposit_amount)
     (< c39c1f7a5_received_amount c39c1f7a5_deposit_amount)))
(define-fun report_safety () Bool (=> (and c39c1f7a5_is_fee_on_transfer_token
         (= 10000 c39c1f7a5_deposit_amount)
         (< c39c1f7a5_received_amount c39c1f7a5_deposit_amount))
    (and (<= c39c1f7a5_credited_amount c39c1f7a5_received_amount)
         (not c39c1f7a5_recorded_balance_exceeds_holdings))))
(define-fun report_effects () Bool (and c39c1f7a5_is_fee_on_transfer_token
     (= 10000 c39c1f7a5_deposit_amount)
     (< c39c1f7a5_received_amount c39c1f7a5_deposit_amount)
     (not (and (<= c39c1f7a5_credited_amount c39c1f7a5_received_amount)
               (not c39c1f7a5_recorded_balance_exceeds_holdings)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
