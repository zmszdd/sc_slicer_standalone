; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c662da937_contract_received_tokens () Int)
(declare-fun c662da937_dispute_amount_sent_tokens () Int)
(declare-fun c662da937_dispute_token_is_fot () Bool)
(declare-fun c662da937_recovery_path_available () Bool)
(assert
 (= c662da937_contract_received_tokens c662da937_contract_received_tokens))
(assert
 (= c662da937_dispute_amount_sent_tokens c662da937_dispute_amount_sent_tokens))
(assert
 (= c662da937_dispute_token_is_fot c662da937_dispute_token_is_fot))
(assert
 (= c662da937_recovery_path_available c662da937_recovery_path_available))
(define-fun report_preconditions () Bool (and c662da937_dispute_token_is_fot
     (= 1000 c662da937_dispute_amount_sent_tokens)
     (= 990 c662da937_contract_received_tokens)))
(define-fun report_safety () Bool (=> (and c662da937_dispute_token_is_fot
         (= 1000 c662da937_dispute_amount_sent_tokens)
         (= 990 c662da937_contract_received_tokens))
    c662da937_recovery_path_available))
(define-fun report_effects () Bool (and c662da937_dispute_token_is_fot
     (= 1000 c662da937_dispute_amount_sent_tokens)
     (= 990 c662da937_contract_received_tokens)
     (not c662da937_recovery_path_available)))
