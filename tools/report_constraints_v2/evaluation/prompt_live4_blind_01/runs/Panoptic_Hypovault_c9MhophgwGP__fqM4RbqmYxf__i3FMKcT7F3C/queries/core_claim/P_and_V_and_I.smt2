; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun first_fulfill_total_assets () Int)
(declare-fun deposit_fulfillment_completed () Bool)
(declare-fun shares_received_zero () Bool)
(assert
 (= first_fulfill_total_assets first_fulfill_total_assets))
(assert
 (= deposit_fulfillment_completed deposit_fulfillment_completed))
(assert
 (= shares_received_zero shares_received_zero))
(define-fun report_preconditions () Bool (= 1 first_fulfill_total_assets))
(define-fun report_safety () Bool (=> (= 1 first_fulfill_total_assets) deposit_fulfillment_completed))
(define-fun report_effects () Bool (and (= 1 first_fulfill_total_assets) (not deposit_fulfillment_completed)))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
