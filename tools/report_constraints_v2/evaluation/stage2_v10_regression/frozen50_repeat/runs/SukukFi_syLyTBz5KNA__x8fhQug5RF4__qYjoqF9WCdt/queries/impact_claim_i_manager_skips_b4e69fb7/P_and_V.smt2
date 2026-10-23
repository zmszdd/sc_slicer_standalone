; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cab6bcf6d_alice_in_active_set () Bool)
(declare-fun cab6bcf6d_claimable_assets () Int)
(declare-fun cab6bcf6d_manager_sees_alice () Bool)
(declare-fun cab6bcf6d_pending_assets () Int)
(assert
 (= cab6bcf6d_alice_in_active_set cab6bcf6d_alice_in_active_set))
(assert
 (= cab6bcf6d_claimable_assets cab6bcf6d_claimable_assets))
(assert
 (= cab6bcf6d_manager_sees_alice cab6bcf6d_manager_sees_alice))
(assert
 (= cab6bcf6d_pending_assets cab6bcf6d_pending_assets))
(define-fun report_preconditions () Bool (and (= 100 cab6bcf6d_pending_assets)
     (= 100 cab6bcf6d_claimable_assets)
     (= 50 cab6bcf6d_pending_assets)
     cab6bcf6d_alice_in_active_set))
(define-fun report_safety () Bool (=> (and (< 0 cab6bcf6d_pending_assets) cab6bcf6d_alice_in_active_set)
    cab6bcf6d_manager_sees_alice))
(define-fun report_effects () Bool (and (< 0 cab6bcf6d_pending_assets)
     cab6bcf6d_alice_in_active_set
     (not cab6bcf6d_manager_sees_alice)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
