; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun paused () Bool)
(declare-fun escrow_entrypoints_live () Bool)
(declare-fun escrow_state_changed () Bool)
(assert
 (= paused paused))
(assert
 (= escrow_entrypoints_live escrow_entrypoints_live))
(assert
 (= escrow_state_changed escrow_state_changed))
(define-fun report_preconditions () Bool (and paused escrow_entrypoints_live))
(define-fun report_safety () Bool (=> paused (not escrow_state_changed)))
(define-fun report_effects () Bool (and paused escrow_state_changed))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
