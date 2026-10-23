; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3f8ec1d3_alice_claimable_assets () Int)
(declare-fun c3f8ec1d3_alice_in_active_set_after_claim () Bool)
(declare-fun c3f8ec1d3_alice_pending_assets () Int)
(declare-fun c3f8ec1d3_alice_pending_assets_after_claim () Int)
(assert
 (= c3f8ec1d3_alice_claimable_assets c3f8ec1d3_alice_claimable_assets))
(assert
 (= c3f8ec1d3_alice_in_active_set_after_claim c3f8ec1d3_alice_in_active_set_after_claim))
(assert
 (= c3f8ec1d3_alice_pending_assets c3f8ec1d3_alice_pending_assets))
(assert
 (= c3f8ec1d3_alice_pending_assets_after_claim c3f8ec1d3_alice_pending_assets_after_claim))
(define-fun report_preconditions () Bool (and (= 100 c3f8ec1d3_alice_pending_assets)
     (= 100 c3f8ec1d3_alice_claimable_assets)
     (= 50 c3f8ec1d3_alice_pending_assets)))
(define-fun report_safety () Bool (=> (and (< 0 c3f8ec1d3_alice_pending_assets_after_claim)
         (= 100 c3f8ec1d3_alice_claimable_assets))
    c3f8ec1d3_alice_in_active_set_after_claim))
(define-fun report_effects () Bool (and (< 0 c3f8ec1d3_alice_pending_assets_after_claim)
     (= 100 c3f8ec1d3_alice_claimable_assets)
     (not c3f8ec1d3_alice_in_active_set_after_claim)))
(assert report_preconditions)
(check-sat)
