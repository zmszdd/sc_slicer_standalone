; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c5ccd33a6_fee_nav_integrations_wrong_observed () Bool)
(declare-fun c5ccd33a6_share_price_accounting_corrupted () Bool)
(declare-fun c5ccd33a6_total_assets_before_first_fulfilment () Int)
(assert
 (= c5ccd33a6_fee_nav_integrations_wrong_observed c5ccd33a6_fee_nav_integrations_wrong_observed))
(assert
 (= c5ccd33a6_share_price_accounting_corrupted c5ccd33a6_share_price_accounting_corrupted))
(assert
 (= c5ccd33a6_total_assets_before_first_fulfilment c5ccd33a6_total_assets_before_first_fulfilment))
(define-fun report_preconditions () Bool (= 1 c5ccd33a6_total_assets_before_first_fulfilment))
(define-fun report_safety () Bool (=> c5ccd33a6_fee_nav_integrations_wrong_observed
    (=> (= 1 c5ccd33a6_total_assets_before_first_fulfilment)
        (not c5ccd33a6_share_price_accounting_corrupted))))
(define-fun report_effects () Bool (and c5ccd33a6_fee_nav_integrations_wrong_observed
     (= 1 c5ccd33a6_total_assets_before_first_fulfilment)
     (not (not c5ccd33a6_share_price_accounting_corrupted))))
