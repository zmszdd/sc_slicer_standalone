; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cc50462fd_gross_amount_at_minimum () Bool)
(declare-fun cc50462fd_net_emits_below_floor () Bool)
(declare-fun cc50462fd_nonzero_protocol_fees () Bool)
(assert
 (= cc50462fd_gross_amount_at_minimum cc50462fd_gross_amount_at_minimum))
(assert
 (= cc50462fd_net_emits_below_floor cc50462fd_net_emits_below_floor))
(assert
 (= cc50462fd_nonzero_protocol_fees cc50462fd_nonzero_protocol_fees))
(define-fun report_preconditions () Bool (and cc50462fd_gross_amount_at_minimum cc50462fd_nonzero_protocol_fees))
(define-fun report_safety () Bool (=> (and cc50462fd_gross_amount_at_minimum cc50462fd_nonzero_protocol_fees)
    (not cc50462fd_net_emits_below_floor)))
(define-fun report_effects () Bool (and cc50462fd_gross_amount_at_minimum
     cc50462fd_nonzero_protocol_fees
     (not (not cc50462fd_net_emits_below_floor))))
