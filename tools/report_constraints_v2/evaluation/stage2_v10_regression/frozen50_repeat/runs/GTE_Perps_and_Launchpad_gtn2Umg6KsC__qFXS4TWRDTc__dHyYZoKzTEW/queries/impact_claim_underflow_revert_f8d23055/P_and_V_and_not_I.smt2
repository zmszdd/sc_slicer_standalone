; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c54d27382_claim_completed () Bool)
(declare-fun c54d27382_fake_token_approved () Bool)
(declare-fun c54d27382_pool_total_shares () Int)
(declare-fun c54d27382_real_quote_pending () Int)
(declare-fun c54d27382_underflow_revert_occurred () Bool)
(assert
 (= c54d27382_claim_completed c54d27382_claim_completed))
(assert
 (= c54d27382_fake_token_approved c54d27382_fake_token_approved))
(assert
 (= c54d27382_pool_total_shares c54d27382_pool_total_shares))
(assert
 (= c54d27382_real_quote_pending c54d27382_real_quote_pending))
(assert
 (= c54d27382_underflow_revert_occurred c54d27382_underflow_revert_occurred))
(define-fun report_preconditions () Bool (and (< 0 c54d27382_pool_total_shares)
     c54d27382_fake_token_approved
     (= 0 c54d27382_real_quote_pending)))
(define-fun report_safety () Bool (=> (and (< 0 c54d27382_pool_total_shares)
         c54d27382_fake_token_approved
         (= 0 c54d27382_real_quote_pending))
    (and c54d27382_claim_completed (not c54d27382_underflow_revert_occurred))))
(define-fun report_effects () Bool (and (< 0 c54d27382_pool_total_shares)
     c54d27382_fake_token_approved
     (= 0 c54d27382_real_quote_pending)
     (not (and c54d27382_claim_completed
               (not c54d27382_underflow_revert_occurred)))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
