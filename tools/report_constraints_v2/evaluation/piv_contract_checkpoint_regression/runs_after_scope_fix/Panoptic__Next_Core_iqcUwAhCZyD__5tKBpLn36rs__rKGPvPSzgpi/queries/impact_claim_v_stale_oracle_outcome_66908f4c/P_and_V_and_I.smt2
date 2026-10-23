; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c85750130_spot_ema_moves_faster () Bool)
(declare-fun c85750130_stale_gate_outcome_matches_intended () Bool)
(declare-fun c85750130_twap_feeds_liquidation () Bool)
(assert
 (= c85750130_spot_ema_moves_faster c85750130_spot_ema_moves_faster))
(assert
 (= c85750130_stale_gate_outcome_matches_intended c85750130_stale_gate_outcome_matches_intended))
(assert
 (= c85750130_twap_feeds_liquidation c85750130_twap_feeds_liquidation))
(define-fun report_preconditions () Bool (and c85750130_spot_ema_moves_faster c85750130_twap_feeds_liquidation))
(define-fun report_safety () Bool (=> (and c85750130_spot_ema_moves_faster c85750130_twap_feeds_liquidation)
    c85750130_stale_gate_outcome_matches_intended))
(define-fun report_effects () Bool (and c85750130_spot_ema_moves_faster
     c85750130_twap_feeds_liquidation
     (not c85750130_stale_gate_outcome_matches_intended)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
