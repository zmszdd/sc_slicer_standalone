; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c641fd0ed_gross_amount_at_minimum () Bool)
(declare-fun c641fd0ed_net_amount_below_floor () Bool)
(declare-fun c641fd0ed_nonzero_fees_apply () Bool)
(assert
 (= c641fd0ed_gross_amount_at_minimum c641fd0ed_gross_amount_at_minimum))
(assert
 (= c641fd0ed_net_amount_below_floor c641fd0ed_net_amount_below_floor))
(assert
 (= c641fd0ed_nonzero_fees_apply c641fd0ed_nonzero_fees_apply))
(define-fun report_preconditions () Bool (and c641fd0ed_gross_amount_at_minimum c641fd0ed_nonzero_fees_apply))
(define-fun report_safety () Bool (=> (and c641fd0ed_gross_amount_at_minimum c641fd0ed_nonzero_fees_apply)
    (not c641fd0ed_net_amount_below_floor)))
(define-fun report_effects () Bool (and c641fd0ed_gross_amount_at_minimum
     c641fd0ed_nonzero_fees_apply
     (not (not c641fd0ed_net_amount_below_floor))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
