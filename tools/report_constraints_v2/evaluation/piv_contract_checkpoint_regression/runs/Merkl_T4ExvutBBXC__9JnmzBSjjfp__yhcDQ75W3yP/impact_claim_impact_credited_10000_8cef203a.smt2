; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3b7719f8_creator_balance_credited () Int)
(declare-fun c3b7719f8_deposit_amount () Int)
(declare-fun c3b7719f8_is_fee_on_transfer_token () Bool)
(declare-fun c3b7719f8_tokens_received_by_contract () Int)
(assert
 (= c3b7719f8_creator_balance_credited c3b7719f8_creator_balance_credited))
(assert
 (= c3b7719f8_deposit_amount c3b7719f8_deposit_amount))
(assert
 (= c3b7719f8_is_fee_on_transfer_token c3b7719f8_is_fee_on_transfer_token))
(assert
 (= c3b7719f8_tokens_received_by_contract c3b7719f8_tokens_received_by_contract))
(define-fun report_preconditions () Bool (and c3b7719f8_is_fee_on_transfer_token
     (= 10000 c3b7719f8_deposit_amount)
     (= 9900 c3b7719f8_tokens_received_by_contract)
     (< c3b7719f8_tokens_received_by_contract c3b7719f8_deposit_amount)))
(define-fun report_safety () Bool (=> (and c3b7719f8_is_fee_on_transfer_token
         (= 10000 c3b7719f8_deposit_amount)
         (= 9900 c3b7719f8_tokens_received_by_contract))
    (<= c3b7719f8_creator_balance_credited
        c3b7719f8_tokens_received_by_contract)))
(define-fun report_effects () Bool (and c3b7719f8_is_fee_on_transfer_token
     (= 10000 c3b7719f8_deposit_amount)
     (= 9900 c3b7719f8_tokens_received_by_contract)
     (not (<= c3b7719f8_creator_balance_credited
              c3b7719f8_tokens_received_by_contract))))
