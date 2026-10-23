; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7ffa83a8_actual_holdings_after () Int)
(declare-fun c7ffa83a8_deposit_amount () Int)
(declare-fun c7ffa83a8_is_fee_on_transfer_token () Bool)
(declare-fun c7ffa83a8_received_amount () Int)
(declare-fun c7ffa83a8_recorded_balance_after () Int)
(assert
 (= c7ffa83a8_actual_holdings_after c7ffa83a8_actual_holdings_after))
(assert
 (= c7ffa83a8_deposit_amount c7ffa83a8_deposit_amount))
(assert
 (= c7ffa83a8_is_fee_on_transfer_token c7ffa83a8_is_fee_on_transfer_token))
(assert
 (= c7ffa83a8_received_amount c7ffa83a8_received_amount))
(assert
 (= c7ffa83a8_recorded_balance_after c7ffa83a8_recorded_balance_after))
(define-fun report_preconditions () Bool (and c7ffa83a8_is_fee_on_transfer_token
     (= 10000 c7ffa83a8_deposit_amount)
     (= 9900 c7ffa83a8_received_amount)))
(define-fun report_safety () Bool (=> (and c7ffa83a8_is_fee_on_transfer_token
         (= 10000 c7ffa83a8_deposit_amount)
         (= 9900 c7ffa83a8_received_amount))
    (<= c7ffa83a8_recorded_balance_after c7ffa83a8_actual_holdings_after)))
(define-fun report_effects () Bool (and c7ffa83a8_is_fee_on_transfer_token
     (= 10000 c7ffa83a8_deposit_amount)
     (= 9900 c7ffa83a8_received_amount)
     (not (<= c7ffa83a8_recorded_balance_after c7ffa83a8_actual_holdings_after))))
