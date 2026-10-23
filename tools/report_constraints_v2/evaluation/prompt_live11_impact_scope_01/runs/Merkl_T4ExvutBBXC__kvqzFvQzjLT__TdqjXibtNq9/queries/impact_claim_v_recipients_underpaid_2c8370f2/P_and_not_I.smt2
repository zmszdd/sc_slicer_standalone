; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9d0dd3cf_gross_amount_at_minimum () Bool)
(declare-fun c9d0dd3cf_net_amount_below_floor () Bool)
(declare-fun c9d0dd3cf_nonzero_protocol_fees () Bool)
(declare-fun c9d0dd3cf_recipients_underpaid () Bool)
(assert
 (= c9d0dd3cf_gross_amount_at_minimum c9d0dd3cf_gross_amount_at_minimum))
(assert
 (= c9d0dd3cf_net_amount_below_floor c9d0dd3cf_net_amount_below_floor))
(assert
 (= c9d0dd3cf_nonzero_protocol_fees c9d0dd3cf_nonzero_protocol_fees))
(assert
 (= c9d0dd3cf_recipients_underpaid c9d0dd3cf_recipients_underpaid))
(define-fun report_preconditions () Bool (and c9d0dd3cf_gross_amount_at_minimum c9d0dd3cf_nonzero_protocol_fees))
(define-fun report_safety () Bool (=> c9d0dd3cf_net_amount_below_floor (not c9d0dd3cf_recipients_underpaid)))
(define-fun report_effects () Bool (and c9d0dd3cf_net_amount_below_floor
     (not (not c9d0dd3cf_recipients_underpaid))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
