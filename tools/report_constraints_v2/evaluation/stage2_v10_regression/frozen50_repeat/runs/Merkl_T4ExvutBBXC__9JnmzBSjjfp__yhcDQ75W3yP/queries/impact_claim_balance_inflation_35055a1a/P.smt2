; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7ffa83a8_actual_contract_holdings () Int)
(declare-fun c7ffa83a8_deposit_amount () Int)
(declare-fun c7ffa83a8_is_fee_on_transfer_token () Bool)
(declare-fun c7ffa83a8_recorded_creator_balance () Int)
(assert
 (= c7ffa83a8_actual_contract_holdings c7ffa83a8_actual_contract_holdings))
(assert
 (= c7ffa83a8_deposit_amount c7ffa83a8_deposit_amount))
(assert
 (= c7ffa83a8_is_fee_on_transfer_token c7ffa83a8_is_fee_on_transfer_token))
(assert
 (= c7ffa83a8_recorded_creator_balance c7ffa83a8_recorded_creator_balance))
(define-fun report_preconditions () Bool (and c7ffa83a8_is_fee_on_transfer_token (= 10000 c7ffa83a8_deposit_amount)))
(define-fun report_safety () Bool (=> (and c7ffa83a8_is_fee_on_transfer_token (= 10000 c7ffa83a8_deposit_amount))
    (<= c7ffa83a8_recorded_creator_balance c7ffa83a8_actual_contract_holdings)))
(define-fun report_effects () Bool (and c7ffa83a8_is_fee_on_transfer_token
     (= 10000 c7ffa83a8_deposit_amount)
     (not (<= c7ffa83a8_recorded_creator_balance
              c7ffa83a8_actual_contract_holdings))))
(assert report_preconditions)
(check-sat)
(get-model)
