; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8cde5597_claim_completed () Bool)
(declare-fun c8cde5597_claim_revert_observed () Bool)
(declare-fun c8cde5597_fake_token_approved () Bool)
(declare-fun c8cde5597_total_shares () Int)
(assert
 (= c8cde5597_claim_completed c8cde5597_claim_completed))
(assert
 (= c8cde5597_claim_revert_observed c8cde5597_claim_revert_observed))
(assert
 (= c8cde5597_fake_token_approved c8cde5597_fake_token_approved))
(assert
 (= c8cde5597_total_shares c8cde5597_total_shares))
(define-fun report_preconditions () Bool (and (< 0 c8cde5597_total_shares) c8cde5597_fake_token_approved))
(define-fun report_safety () Bool (=> (and (< 0 c8cde5597_total_shares) c8cde5597_fake_token_approved)
    (and c8cde5597_claim_completed (not c8cde5597_claim_revert_observed))))
(define-fun report_effects () Bool (and (< 0 c8cde5597_total_shares)
     c8cde5597_fake_token_approved
     (not (and c8cde5597_claim_completed (not c8cde5597_claim_revert_observed)))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
