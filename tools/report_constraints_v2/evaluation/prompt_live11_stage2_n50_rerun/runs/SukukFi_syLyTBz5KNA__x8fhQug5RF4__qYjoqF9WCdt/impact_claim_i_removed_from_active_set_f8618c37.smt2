; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c3e8976f3_alice_in_active_set_after () Bool)
(declare-fun c3e8976f3_alice_in_active_set_before () Bool)
(declare-fun c3e8976f3_claimable_shares () Int)
(declare-fun c3e8976f3_pending_assets () Int)
(declare-fun c3e8976f3_pending_assets_after () Int)
(assert
 (= c3e8976f3_alice_in_active_set_after c3e8976f3_alice_in_active_set_after))
(assert
 (= c3e8976f3_alice_in_active_set_before c3e8976f3_alice_in_active_set_before))
(assert
 (= c3e8976f3_claimable_shares c3e8976f3_claimable_shares))
(assert
 (= c3e8976f3_pending_assets c3e8976f3_pending_assets))
(assert
 (= c3e8976f3_pending_assets_after c3e8976f3_pending_assets_after))
(define-fun report_preconditions () Bool (and (= 50 c3e8976f3_pending_assets)
     (= 100 c3e8976f3_claimable_shares)
     c3e8976f3_alice_in_active_set_before))
(define-fun report_safety () Bool (=> (and (= 50 c3e8976f3_pending_assets) c3e8976f3_alice_in_active_set_before)
    (or (= 0 c3e8976f3_pending_assets_after)
        c3e8976f3_alice_in_active_set_after)))
(define-fun report_effects () Bool (and (= 50 c3e8976f3_pending_assets)
     c3e8976f3_alice_in_active_set_before
     (not (or (= 0 c3e8976f3_pending_assets_after)
              c3e8976f3_alice_in_active_set_after))))
