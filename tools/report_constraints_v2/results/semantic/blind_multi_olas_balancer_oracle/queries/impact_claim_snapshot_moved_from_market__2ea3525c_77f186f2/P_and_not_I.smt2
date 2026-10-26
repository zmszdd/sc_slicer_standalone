; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c22df6241_attacker_controls_pool_spot_regime () Bool)
(declare-fun c22df6241_snapshot_moved_toward_attacker_regime () Bool)
(declare-fun c22df6241_snapshot_steerable_away_from_market_price () Bool)
(assert
 (= c22df6241_attacker_controls_pool_spot_regime c22df6241_attacker_controls_pool_spot_regime))
(assert
 (= c22df6241_snapshot_moved_toward_attacker_regime c22df6241_snapshot_moved_toward_attacker_regime))
(assert
 (= c22df6241_snapshot_steerable_away_from_market_price c22df6241_snapshot_steerable_away_from_market_price))
(define-fun report_preconditions () Bool c22df6241_attacker_controls_pool_spot_regime)
(define-fun report_safety () Bool (=> c22df6241_attacker_controls_pool_spot_regime
    (= c22df6241_snapshot_steerable_away_from_market_price
       c22df6241_snapshot_steerable_away_from_market_price)))
(define-fun report_effects () Bool c22df6241_snapshot_moved_toward_attacker_regime)
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
