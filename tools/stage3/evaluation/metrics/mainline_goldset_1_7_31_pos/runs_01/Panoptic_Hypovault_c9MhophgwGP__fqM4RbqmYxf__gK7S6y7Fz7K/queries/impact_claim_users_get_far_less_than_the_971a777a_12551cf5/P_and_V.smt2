; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc7a4bf49_bootstrap_shares_count () Int)
(declare-fun cc7a4bf49_share_price_inflated () Bool)
(declare-fun cc7a4bf49_unowned_bootstrap_shares () Int)
(declare-fun cc7a4bf49_unowned_shares_in_total_supply () Int)
(assert
 (= cc7a4bf49_bootstrap_shares_count cc7a4bf49_bootstrap_shares_count))
(assert
 (= cc7a4bf49_share_price_inflated cc7a4bf49_share_price_inflated))
(assert
 (= cc7a4bf49_unowned_bootstrap_shares cc7a4bf49_unowned_bootstrap_shares))
(assert
 (= cc7a4bf49_unowned_shares_in_total_supply cc7a4bf49_unowned_shares_in_total_supply))
(define-fun report_preconditions () Bool (and (= 1000000 cc7a4bf49_bootstrap_shares_count)
     (= 1000000 cc7a4bf49_unowned_bootstrap_shares)
     cc7a4bf49_share_price_inflated))
(define-fun report_safety () Bool (=> (= cc7a4bf49_unowned_bootstrap_shares cc7a4bf49_bootstrap_shares_count)
    (= 0 cc7a4bf49_unowned_shares_in_total_supply)))
(define-fun report_effects () Bool (and (= cc7a4bf49_unowned_bootstrap_shares cc7a4bf49_bootstrap_shares_count)
     cc7a4bf49_share_price_inflated
     (not (= 0 cc7a4bf49_unowned_shares_in_total_supply))
     cc7a4bf49_share_price_inflated
     cc7a4bf49_share_price_inflated))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
