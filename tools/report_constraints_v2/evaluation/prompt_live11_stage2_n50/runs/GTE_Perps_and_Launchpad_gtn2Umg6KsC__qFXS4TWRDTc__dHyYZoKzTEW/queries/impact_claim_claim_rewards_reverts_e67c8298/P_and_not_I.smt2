; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c223b5e4a_claim_rewards_reverts_observed () Bool)
(declare-fun c223b5e4a_fake_token_approved () Bool)
(declare-fun c223b5e4a_pool_total_shares () Int)
(assert
 (= c223b5e4a_claim_rewards_reverts_observed c223b5e4a_claim_rewards_reverts_observed))
(assert
 (= c223b5e4a_fake_token_approved c223b5e4a_fake_token_approved))
(assert
 (= c223b5e4a_pool_total_shares c223b5e4a_pool_total_shares))
(define-fun report_preconditions () Bool (and (< 0 c223b5e4a_pool_total_shares) c223b5e4a_fake_token_approved))
(define-fun report_safety () Bool (=> (and (< 0 c223b5e4a_pool_total_shares) c223b5e4a_fake_token_approved)
    (not c223b5e4a_claim_rewards_reverts_observed)))
(define-fun report_effects () Bool (and (< 0 c223b5e4a_pool_total_shares)
     c223b5e4a_fake_token_approved
     (not (not c223b5e4a_claim_rewards_reverts_observed))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
