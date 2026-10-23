; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2178f68e_amounts_disjoint_bits () Bool)
(declare-fun c2178f68e_match_reverted_zero_cost_trade () Bool)
(assert
 (= c2178f68e_amounts_disjoint_bits c2178f68e_amounts_disjoint_bits))
(assert
 (= c2178f68e_match_reverted_zero_cost_trade c2178f68e_match_reverted_zero_cost_trade))
(define-fun report_preconditions () Bool c2178f68e_amounts_disjoint_bits)
(define-fun report_safety () Bool (=> c2178f68e_match_reverted_zero_cost_trade
    (=> c2178f68e_amounts_disjoint_bits
        (not c2178f68e_match_reverted_zero_cost_trade))))
(define-fun report_effects () Bool (and c2178f68e_match_reverted_zero_cost_trade
     c2178f68e_amounts_disjoint_bits
     (not (not c2178f68e_match_reverted_zero_cost_trade))))
(assert report_preconditions)
(check-sat)
(get-model)
