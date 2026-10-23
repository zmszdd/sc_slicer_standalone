; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbcf53dfd_spot_ema_moves_short_horizon () Bool)
(declare-fun cbcf53dfd_spot_ema_weight_in_twap () Int)
(declare-fun cbcf53dfd_twap_feeds_solvency_and_stale_gate () Bool)
(assert
 (= cbcf53dfd_spot_ema_moves_short_horizon cbcf53dfd_spot_ema_moves_short_horizon))
(assert
 (= cbcf53dfd_spot_ema_weight_in_twap cbcf53dfd_spot_ema_weight_in_twap))
(assert
 (= cbcf53dfd_twap_feeds_solvency_and_stale_gate cbcf53dfd_twap_feeds_solvency_and_stale_gate))
(define-fun report_preconditions () Bool (and cbcf53dfd_spot_ema_moves_short_horizon
     cbcf53dfd_twap_feeds_solvency_and_stale_gate))
(define-fun report_safety () Bool (=> (and cbcf53dfd_spot_ema_moves_short_horizon
         cbcf53dfd_twap_feeds_solvency_and_stale_gate)
    (= 0 cbcf53dfd_spot_ema_weight_in_twap)))
(define-fun report_effects () Bool (and cbcf53dfd_spot_ema_moves_short_horizon
     cbcf53dfd_twap_feeds_solvency_and_stale_gate
     (not (= 0 cbcf53dfd_spot_ema_weight_in_twap))))
