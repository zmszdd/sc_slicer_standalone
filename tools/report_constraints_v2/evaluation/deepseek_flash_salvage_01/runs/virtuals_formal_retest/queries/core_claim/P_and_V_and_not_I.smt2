; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun caller_has_executor_role () Bool)
(declare-fun klast_is_initial_product () Bool)
(declare-fun price_incorrect_after_trade () Bool)
(assert
 (= caller_has_executor_role caller_has_executor_role))
(assert
 (= klast_is_initial_product klast_is_initial_product))
(assert
 (= price_incorrect_after_trade price_incorrect_after_trade))
(define-fun report_preconditions () Bool (and caller_has_executor_role klast_is_initial_product))
(define-fun report_safety () Bool (=> klast_is_initial_product price_incorrect_after_trade))
(define-fun report_effects () Bool (and klast_is_initial_product (not price_incorrect_after_trade)))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
