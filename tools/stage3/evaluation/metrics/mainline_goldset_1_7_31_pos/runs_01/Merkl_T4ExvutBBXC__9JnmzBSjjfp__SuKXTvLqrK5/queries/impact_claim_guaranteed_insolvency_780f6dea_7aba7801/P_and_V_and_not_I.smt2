; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c8af04b98_actually_received_amount () Int)
(declare-fun c8af04b98_credited_amount () Int)
(declare-fun c8af04b98_fot_token_whitelisted () Bool)
(declare-fun c8af04b98_insolvency_occurred () Bool)
(declare-fun c8af04b98_transfer_delivered_amount () Int)
(declare-fun c8af04b98_transfer_requested_amount () Int)
(assert
 (= c8af04b98_actually_received_amount c8af04b98_actually_received_amount))
(assert
 (= c8af04b98_credited_amount c8af04b98_credited_amount))
(assert
 (= c8af04b98_fot_token_whitelisted c8af04b98_fot_token_whitelisted))
(assert
 (= c8af04b98_insolvency_occurred c8af04b98_insolvency_occurred))
(assert
 (= c8af04b98_transfer_delivered_amount c8af04b98_transfer_delivered_amount))
(assert
 (= c8af04b98_transfer_requested_amount c8af04b98_transfer_requested_amount))
(define-fun report_preconditions () Bool (and c8af04b98_fot_token_whitelisted
     (< c8af04b98_transfer_delivered_amount c8af04b98_transfer_requested_amount)))
(define-fun report_safety () Bool (=> c8af04b98_fot_token_whitelisted
    (= c8af04b98_credited_amount c8af04b98_actually_received_amount)))
(define-fun report_effects () Bool (and c8af04b98_fot_token_whitelisted
     (not (= c8af04b98_credited_amount c8af04b98_actually_received_amount))
     c8af04b98_insolvency_occurred))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
