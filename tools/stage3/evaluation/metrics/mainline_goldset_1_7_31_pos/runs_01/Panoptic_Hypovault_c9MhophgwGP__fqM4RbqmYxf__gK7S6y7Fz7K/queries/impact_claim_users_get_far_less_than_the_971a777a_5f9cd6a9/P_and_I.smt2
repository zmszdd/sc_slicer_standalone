; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8ba008b3_bootstrap_shares_allocated () Bool)
(declare-fun c8ba008b3_phantom_shares_owned () Bool)
(declare-fun c8ba008b3_share_price_inflated () Bool)
(declare-fun c8ba008b3_sum_of_balances () Int)
(declare-fun c8ba008b3_total_supply_value () Int)
(assert
 (= c8ba008b3_bootstrap_shares_allocated c8ba008b3_bootstrap_shares_allocated))
(assert
 (= c8ba008b3_phantom_shares_owned c8ba008b3_phantom_shares_owned))
(assert
 (= c8ba008b3_share_price_inflated c8ba008b3_share_price_inflated))
(assert
 (= c8ba008b3_sum_of_balances c8ba008b3_sum_of_balances))
(assert
 (= c8ba008b3_total_supply_value c8ba008b3_total_supply_value))
(define-fun report_preconditions () Bool (and (not c8ba008b3_bootstrap_shares_allocated)
     (not c8ba008b3_phantom_shares_owned)))
(define-fun report_safety () Bool (=> (not c8ba008b3_bootstrap_shares_allocated)
    (= c8ba008b3_total_supply_value c8ba008b3_sum_of_balances)))
(define-fun report_effects () Bool (and (not c8ba008b3_bootstrap_shares_allocated)
     (not (= c8ba008b3_total_supply_value c8ba008b3_sum_of_balances))
     c8ba008b3_share_price_inflated
     c8ba008b3_share_price_inflated))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
