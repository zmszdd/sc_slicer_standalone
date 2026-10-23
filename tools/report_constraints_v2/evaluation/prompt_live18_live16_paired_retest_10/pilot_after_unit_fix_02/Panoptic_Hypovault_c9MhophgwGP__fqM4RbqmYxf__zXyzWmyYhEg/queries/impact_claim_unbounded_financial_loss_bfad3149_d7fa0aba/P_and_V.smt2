; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c925cf983_subsequent_deposits_drainable () Bool)
(declare-fun c925cf983_total_assets_before_first_deposit () Int)
(declare-fun c925cf983_total_supply_at_construction () Int)
(declare-fun c925cf983_zero_assets_expected () Int)
(declare-fun c925cf983_zero_supply_expected () Int)
(assert
 (= c925cf983_subsequent_deposits_drainable c925cf983_subsequent_deposits_drainable))
(assert
 (= c925cf983_total_assets_before_first_deposit c925cf983_total_assets_before_first_deposit))
(assert
 (= c925cf983_total_supply_at_construction c925cf983_total_supply_at_construction))
(assert
 (= c925cf983_zero_assets_expected c925cf983_zero_assets_expected))
(assert
 (= c925cf983_zero_supply_expected c925cf983_zero_supply_expected))
(define-fun report_preconditions () Bool (and (= 1000000 c925cf983_total_supply_at_construction)
     (= 0 c925cf983_total_assets_before_first_deposit)))
(define-fun report_safety () Bool (let ((a!1 (=> c925cf983_subsequent_deposits_drainable
               (=> (and (= 0 c925cf983_total_assets_before_first_deposit)
                        (= 1000000 c925cf983_total_supply_at_construction))
                   (= c925cf983_total_supply_at_construction
                      c925cf983_zero_supply_expected)))))
  (=> (and (= 0 c925cf983_zero_supply_expected)
           (= 0 c925cf983_zero_assets_expected))
      a!1)))
(define-fun report_effects () Bool (and (= 0 c925cf983_zero_supply_expected)
     (= 0 c925cf983_zero_assets_expected)
     c925cf983_subsequent_deposits_drainable
     (= 0 c925cf983_total_assets_before_first_deposit)
     (= 1000000 c925cf983_total_supply_at_construction)
     (not (= c925cf983_total_supply_at_construction
             c925cf983_zero_supply_expected))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
