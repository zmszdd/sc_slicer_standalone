; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun recipient_set () Bool)
(declare-fun recipient_validation_reverts () Bool)
(declare-fun operator_claim_called () Bool)
(declare-fun claim_amount () Int)
(declare-fun daily_limit () Int)
(declare-fun claim_succeeds () Bool)
(assert
 (= recipient_set recipient_set))
(assert
 (= recipient_validation_reverts recipient_validation_reverts))
(assert
 (= operator_claim_called operator_claim_called))
(assert
 (= claim_amount claim_amount))
(assert
 (= daily_limit daily_limit))
(assert
 (= claim_succeeds claim_succeeds))
(define-fun report_preconditions () Bool (and recipient_set
     recipient_validation_reverts
     operator_claim_called
     (< 1000 claim_amount)))
(define-fun report_safety () Bool (=> (and recipient_set
         recipient_validation_reverts
         operator_claim_called
         (< 1000 claim_amount))
    (not claim_succeeds)))
(define-fun report_effects () Bool (and recipient_set
     recipient_validation_reverts
     operator_claim_called
     (< 1000 claim_amount)
     (not (not claim_succeeds))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
