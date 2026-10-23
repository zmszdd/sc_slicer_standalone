; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c02170003_campaign_funding_failed () Bool)
(declare-fun c02170003_credited_balance () Int)
(declare-fun c02170003_deposit_amount () Int)
(declare-fun c02170003_is_fee_on_transfer_token () Bool)
(declare-fun c02170003_received_amount () Int)
(assert
 (= c02170003_campaign_funding_failed c02170003_campaign_funding_failed))
(assert
 (= c02170003_credited_balance c02170003_credited_balance))
(assert
 (= c02170003_deposit_amount c02170003_deposit_amount))
(assert
 (= c02170003_is_fee_on_transfer_token c02170003_is_fee_on_transfer_token))
(assert
 (= c02170003_received_amount c02170003_received_amount))
(define-fun report_preconditions () Bool (and c02170003_is_fee_on_transfer_token
     (= 10000 c02170003_deposit_amount)
     (= 9900 c02170003_received_amount)))
(define-fun report_safety () Bool (=> (and c02170003_is_fee_on_transfer_token
         (= 10000 c02170003_deposit_amount)
         (= 9900 c02170003_received_amount))
    (and (<= c02170003_credited_balance c02170003_received_amount)
         (not c02170003_campaign_funding_failed))))
(define-fun report_effects () Bool (and c02170003_is_fee_on_transfer_token
     (= 10000 c02170003_deposit_amount)
     (= 9900 c02170003_received_amount)
     (not (and (<= c02170003_credited_balance c02170003_received_amount)
               (not c02170003_campaign_funding_failed)))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
