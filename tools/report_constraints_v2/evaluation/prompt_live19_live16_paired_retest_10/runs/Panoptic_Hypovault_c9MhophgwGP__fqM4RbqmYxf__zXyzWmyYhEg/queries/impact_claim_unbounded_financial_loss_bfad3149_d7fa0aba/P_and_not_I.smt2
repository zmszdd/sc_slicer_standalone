; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c925cf983_total_supply_at_bootstrap () Int)
(declare-fun c925cf983_unbounded_loss_possible () Bool)
(declare-fun c925cf983_underlying_assets_at_bootstrap () Int)
(declare-fun c925cf983_zero_assets () Int)
(declare-fun c925cf983_zero_supply () Int)
(assert
 (= c925cf983_total_supply_at_bootstrap c925cf983_total_supply_at_bootstrap))
(assert
 (= c925cf983_unbounded_loss_possible c925cf983_unbounded_loss_possible))
(assert
 (= c925cf983_underlying_assets_at_bootstrap c925cf983_underlying_assets_at_bootstrap))
(assert
 (= c925cf983_zero_assets c925cf983_zero_assets))
(assert
 (= c925cf983_zero_supply c925cf983_zero_supply))
(define-fun report_preconditions () Bool (and (= 1000000 c925cf983_total_supply_at_bootstrap)
     (= c925cf983_underlying_assets_at_bootstrap c925cf983_zero_assets)))
(define-fun report_safety () Bool (=> c925cf983_unbounded_loss_possible
    (=> (= c925cf983_underlying_assets_at_bootstrap c925cf983_zero_assets)
        (= c925cf983_total_supply_at_bootstrap c925cf983_zero_supply))))
(define-fun report_effects () Bool (and c925cf983_unbounded_loss_possible
     (= c925cf983_underlying_assets_at_bootstrap c925cf983_zero_assets)
     (not (= c925cf983_total_supply_at_bootstrap c925cf983_zero_supply))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
