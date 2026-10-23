; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c9e8a925e_legitimate_trade_rejected () Bool)
(declare-fun c9e8a925e_limit_match_in_progress () Bool)
(declare-fun c9e8a925e_matched_amounts_disjoint_bits () Bool)
(declare-fun c9e8a925e_unexplained_failure_observed () Bool)
(assert
 (= c9e8a925e_legitimate_trade_rejected c9e8a925e_legitimate_trade_rejected))
(assert
 (= c9e8a925e_limit_match_in_progress c9e8a925e_limit_match_in_progress))
(assert
 (= c9e8a925e_matched_amounts_disjoint_bits c9e8a925e_matched_amounts_disjoint_bits))
(assert
 (= c9e8a925e_unexplained_failure_observed c9e8a925e_unexplained_failure_observed))
(define-fun report_preconditions () Bool (and c9e8a925e_limit_match_in_progress c9e8a925e_matched_amounts_disjoint_bits))
(define-fun report_safety () Bool (=> c9e8a925e_unexplained_failure_observed
    (=> (and c9e8a925e_limit_match_in_progress
             c9e8a925e_matched_amounts_disjoint_bits)
        (not c9e8a925e_legitimate_trade_rejected))))
(define-fun report_effects () Bool (and c9e8a925e_unexplained_failure_observed
     c9e8a925e_limit_match_in_progress
     c9e8a925e_matched_amounts_disjoint_bits
     (not (not c9e8a925e_legitimate_trade_rejected))))
(assert report_preconditions)
(check-sat)
(get-model)
