; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun ca36ed342_contract_received_tokens () Int)
(declare-fun ca36ed342_dispute_amount_sent_tokens () Int)
(declare-fun ca36ed342_dispute_token_is_fot () Bool)
(declare-fun ca36ed342_resolve_transfer_amount_tokens () Int)
(declare-fun ca36ed342_resolve_transfer_reverted () Bool)
(assert
 (= ca36ed342_contract_received_tokens ca36ed342_contract_received_tokens))
(assert
 (= ca36ed342_dispute_amount_sent_tokens ca36ed342_dispute_amount_sent_tokens))
(assert
 (= ca36ed342_dispute_token_is_fot ca36ed342_dispute_token_is_fot))
(assert
 (= ca36ed342_resolve_transfer_amount_tokens ca36ed342_resolve_transfer_amount_tokens))
(assert
 (= ca36ed342_resolve_transfer_reverted ca36ed342_resolve_transfer_reverted))
(define-fun report_preconditions () Bool (and ca36ed342_dispute_token_is_fot
     (= 1000 ca36ed342_dispute_amount_sent_tokens)
     (= 990 ca36ed342_contract_received_tokens)))
(define-fun report_safety () Bool (=> (and ca36ed342_dispute_token_is_fot
         (= 1000 ca36ed342_dispute_amount_sent_tokens)
         (= 990 ca36ed342_contract_received_tokens))
    (and (= 1000 ca36ed342_resolve_transfer_amount_tokens)
         (not ca36ed342_resolve_transfer_reverted))))
(define-fun report_effects () Bool (and ca36ed342_dispute_token_is_fot
     (= 1000 ca36ed342_dispute_amount_sent_tokens)
     (= 990 ca36ed342_contract_received_tokens)
     (not (and (= 1000 ca36ed342_resolve_transfer_amount_tokens)
               (not ca36ed342_resolve_transfer_reverted)))))
(assert report_preconditions)
(check-sat)
(get-model)
