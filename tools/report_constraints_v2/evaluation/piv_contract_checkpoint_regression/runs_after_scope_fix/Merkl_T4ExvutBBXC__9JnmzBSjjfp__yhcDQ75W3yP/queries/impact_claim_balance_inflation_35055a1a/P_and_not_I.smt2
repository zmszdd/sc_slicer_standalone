; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7ffa83a8_credited_balance () Int)
(declare-fun c7ffa83a8_deposit_amount () Int)
(declare-fun c7ffa83a8_is_fee_on_transfer_token () Bool)
(declare-fun c7ffa83a8_tokens_actually_received () Int)
(assert
 (= c7ffa83a8_credited_balance c7ffa83a8_credited_balance))
(assert
 (= c7ffa83a8_deposit_amount c7ffa83a8_deposit_amount))
(assert
 (= c7ffa83a8_is_fee_on_transfer_token c7ffa83a8_is_fee_on_transfer_token))
(assert
 (= c7ffa83a8_tokens_actually_received c7ffa83a8_tokens_actually_received))
(define-fun report_preconditions () Bool (and c7ffa83a8_is_fee_on_transfer_token
     (= 10000 c7ffa83a8_deposit_amount)
     (= 9900 c7ffa83a8_tokens_actually_received)))
(define-fun report_safety () Bool (=> (and c7ffa83a8_is_fee_on_transfer_token
         (= 10000 c7ffa83a8_deposit_amount)
         (= 9900 c7ffa83a8_tokens_actually_received))
    (<= c7ffa83a8_credited_balance c7ffa83a8_tokens_actually_received)))
(define-fun report_effects () Bool (and c7ffa83a8_is_fee_on_transfer_token
     (= 10000 c7ffa83a8_deposit_amount)
     (= 9900 c7ffa83a8_tokens_actually_received)
     (not (<= c7ffa83a8_credited_balance c7ffa83a8_tokens_actually_received))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
