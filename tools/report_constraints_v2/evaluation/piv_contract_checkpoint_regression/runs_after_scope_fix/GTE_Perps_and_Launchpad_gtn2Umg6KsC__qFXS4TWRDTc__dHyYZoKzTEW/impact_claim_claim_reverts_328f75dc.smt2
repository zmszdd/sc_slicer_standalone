; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8cde5597_claim_reverted () Bool)
(declare-fun c8cde5597_fake_token_approved () Bool)
(declare-fun c8cde5597_pool_total_shares () Int)
(assert
 (= c8cde5597_claim_reverted c8cde5597_claim_reverted))
(assert
 (= c8cde5597_fake_token_approved c8cde5597_fake_token_approved))
(assert
 (= c8cde5597_pool_total_shares c8cde5597_pool_total_shares))
(define-fun report_preconditions () Bool (and (< 0 c8cde5597_pool_total_shares) c8cde5597_fake_token_approved))
(define-fun report_safety () Bool (=> (and (< 0 c8cde5597_pool_total_shares) c8cde5597_fake_token_approved)
    (not c8cde5597_claim_reverted)))
(define-fun report_effects () Bool (and (< 0 c8cde5597_pool_total_shares)
     c8cde5597_fake_token_approved
     (not (not c8cde5597_claim_reverted))))
