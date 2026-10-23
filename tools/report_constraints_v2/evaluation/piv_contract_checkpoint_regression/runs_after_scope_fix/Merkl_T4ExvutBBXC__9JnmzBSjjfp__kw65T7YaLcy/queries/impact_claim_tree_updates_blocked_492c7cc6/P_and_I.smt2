; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c44826396_contract_received_tokens () Int)
(declare-fun c44826396_dispute_amount_sent_tokens () Int)
(declare-fun c44826396_fot_token_is_dispute_token () Bool)
(declare-fun c44826396_tree_updates_blocked_observed () Bool)
(assert
 (= c44826396_contract_received_tokens c44826396_contract_received_tokens))
(assert
 (= c44826396_dispute_amount_sent_tokens c44826396_dispute_amount_sent_tokens))
(assert
 (= c44826396_fot_token_is_dispute_token c44826396_fot_token_is_dispute_token))
(assert
 (= c44826396_tree_updates_blocked_observed c44826396_tree_updates_blocked_observed))
(define-fun report_preconditions () Bool (and c44826396_fot_token_is_dispute_token
     (= 1000 c44826396_dispute_amount_sent_tokens)
     (= 990 c44826396_contract_received_tokens)))
(define-fun report_safety () Bool (=> (and c44826396_fot_token_is_dispute_token
         (= 1000 c44826396_dispute_amount_sent_tokens)
         (= 990 c44826396_contract_received_tokens))
    (not c44826396_tree_updates_blocked_observed)))
(define-fun report_effects () Bool (and c44826396_fot_token_is_dispute_token
     (= 1000 c44826396_dispute_amount_sent_tokens)
     (= 990 c44826396_contract_received_tokens)
     (not (not c44826396_tree_updates_blocked_observed))))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
