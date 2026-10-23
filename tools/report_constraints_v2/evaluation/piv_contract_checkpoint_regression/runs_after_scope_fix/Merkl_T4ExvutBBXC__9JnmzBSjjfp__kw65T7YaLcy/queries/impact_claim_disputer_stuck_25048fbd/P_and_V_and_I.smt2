; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c576698af_contract_received_amount () Int)
(declare-fun c576698af_dispute_amount_sent () Int)
(declare-fun c576698af_dispute_token_is_fot () Bool)
(declare-fun c576698af_disputer_cleared () Bool)
(declare-fun c576698af_disputer_stuck_observed () Bool)
(assert
 (= c576698af_contract_received_amount c576698af_contract_received_amount))
(assert
 (= c576698af_dispute_amount_sent c576698af_dispute_amount_sent))
(assert
 (= c576698af_dispute_token_is_fot c576698af_dispute_token_is_fot))
(assert
 (= c576698af_disputer_cleared c576698af_disputer_cleared))
(assert
 (= c576698af_disputer_stuck_observed c576698af_disputer_stuck_observed))
(define-fun report_preconditions () Bool (and c576698af_dispute_token_is_fot
     (= 1000 c576698af_dispute_amount_sent)
     (= 990 c576698af_contract_received_amount)))
(define-fun report_safety () Bool (=> (and c576698af_dispute_token_is_fot
         (= 1000 c576698af_dispute_amount_sent)
         (= 990 c576698af_contract_received_amount))
    (or c576698af_disputer_cleared (not c576698af_disputer_stuck_observed))))
(define-fun report_effects () Bool (and c576698af_dispute_token_is_fot
     (= 1000 c576698af_dispute_amount_sent)
     (= 990 c576698af_contract_received_amount)
     (not (or c576698af_disputer_cleared
              (not c576698af_disputer_stuck_observed)))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
