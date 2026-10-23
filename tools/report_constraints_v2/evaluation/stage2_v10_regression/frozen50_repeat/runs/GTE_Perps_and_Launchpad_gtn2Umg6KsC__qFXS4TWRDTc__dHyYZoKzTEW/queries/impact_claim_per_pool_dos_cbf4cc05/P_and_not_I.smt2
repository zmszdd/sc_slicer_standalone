; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun caec01250_claim_rewards_reverts () Bool)
(declare-fun caec01250_fake_token_approved () Bool)
(declare-fun caec01250_pool_total_shares () Int)
(declare-fun caec01250_real_quote_pending () Int)
(assert
 (= caec01250_claim_rewards_reverts caec01250_claim_rewards_reverts))
(assert
 (= caec01250_fake_token_approved caec01250_fake_token_approved))
(assert
 (= caec01250_pool_total_shares caec01250_pool_total_shares))
(assert
 (= caec01250_real_quote_pending caec01250_real_quote_pending))
(define-fun report_preconditions () Bool (and (< 0 caec01250_pool_total_shares)
     caec01250_fake_token_approved
     (= 0 caec01250_real_quote_pending)))
(define-fun report_safety () Bool (=> (and (< 0 caec01250_pool_total_shares)
         caec01250_fake_token_approved
         (= 0 caec01250_real_quote_pending))
    (not caec01250_claim_rewards_reverts)))
(define-fun report_effects () Bool (and (< 0 caec01250_pool_total_shares)
     caec01250_fake_token_approved
     (= 0 caec01250_real_quote_pending)
     (not (not caec01250_claim_rewards_reverts))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
