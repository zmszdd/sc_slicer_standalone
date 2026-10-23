; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun caec01250_claim_rewards_reverts () Bool)
(declare-fun caec01250_fake_token_approved () Bool)
(declare-fun caec01250_quote_claims_blocked () Bool)
(declare-fun caec01250_total_shares () Int)
(assert
 (= caec01250_claim_rewards_reverts caec01250_claim_rewards_reverts))
(assert
 (= caec01250_fake_token_approved caec01250_fake_token_approved))
(assert
 (= caec01250_quote_claims_blocked caec01250_quote_claims_blocked))
(assert
 (= caec01250_total_shares caec01250_total_shares))
(define-fun report_preconditions () Bool (and (< 0 caec01250_total_shares) caec01250_fake_token_approved))
(define-fun report_safety () Bool (=> (and (< 0 caec01250_total_shares) caec01250_fake_token_approved)
    (and (not caec01250_claim_rewards_reverts)
         (not caec01250_quote_claims_blocked))))
(define-fun report_effects () Bool (and (< 0 caec01250_total_shares)
     caec01250_fake_token_approved
     (not (and (not caec01250_claim_rewards_reverts)
               (not caec01250_quote_claims_blocked)))))
