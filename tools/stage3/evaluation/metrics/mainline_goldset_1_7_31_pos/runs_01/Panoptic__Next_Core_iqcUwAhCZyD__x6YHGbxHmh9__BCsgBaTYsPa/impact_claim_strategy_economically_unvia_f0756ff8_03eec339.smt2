; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c2ff5ff5a_converted_credit () Int)
(declare-fun c2ff5ff5a_credit_covers_debt () Bool)
(declare-fun c2ff5ff5a_required_collateral () Int)
(declare-fun c2ff5ff5a_strategy_economically_unviable_observed () Bool)
(assert
 (= c2ff5ff5a_converted_credit c2ff5ff5a_converted_credit))
(assert
 (= c2ff5ff5a_credit_covers_debt c2ff5ff5a_credit_covers_debt))
(assert
 (= c2ff5ff5a_required_collateral c2ff5ff5a_required_collateral))
(assert
 (= c2ff5ff5a_strategy_economically_unviable_observed c2ff5ff5a_strategy_economically_unviable_observed))
(define-fun report_preconditions () Bool (and (= 100 c2ff5ff5a_required_collateral)
     (= 105 c2ff5ff5a_converted_credit)
     (> c2ff5ff5a_converted_credit c2ff5ff5a_required_collateral)))
(define-fun report_safety () Bool (=> c2ff5ff5a_credit_covers_debt (>= 1 c2ff5ff5a_required_collateral)))
(define-fun report_effects () Bool (and c2ff5ff5a_credit_covers_debt
     (not (>= 1 c2ff5ff5a_required_collateral))
     c2ff5ff5a_strategy_economically_unviable_observed
     c2ff5ff5a_strategy_economically_unviable_observed))
