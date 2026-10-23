; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7d786a7b_alice_basis_before () Int)
(declare-fun c7d786a7b_alice_market_value () Int)
(declare-fun c7d786a7b_bob_basis () Int)
(declare-fun c7d786a7b_merged_basis_after () Int)
(assert
 (= c7d786a7b_alice_basis_before c7d786a7b_alice_basis_before))
(assert
 (= c7d786a7b_alice_market_value c7d786a7b_alice_market_value))
(assert
 (= c7d786a7b_bob_basis c7d786a7b_bob_basis))
(assert
 (= c7d786a7b_merged_basis_after c7d786a7b_merged_basis_after))
(define-fun report_preconditions () Bool (and (> c7d786a7b_alice_market_value c7d786a7b_alice_basis_before)
     (< 0 c7d786a7b_bob_basis)))
(define-fun report_safety () Bool (=> (= c7d786a7b_merged_basis_after
       (+ c7d786a7b_alice_basis_before c7d786a7b_bob_basis))
    (=> (> c7d786a7b_alice_market_value c7d786a7b_alice_basis_before)
        (< c7d786a7b_merged_basis_after c7d786a7b_alice_market_value))))
(define-fun report_effects () Bool (and (= c7d786a7b_merged_basis_after
        (+ c7d786a7b_alice_basis_before c7d786a7b_bob_basis))
     (> c7d786a7b_alice_market_value c7d786a7b_alice_basis_before)
     (not (< c7d786a7b_merged_basis_after c7d786a7b_alice_market_value))))
(assert report_preconditions)
(assert report_effects)
(assert (not report_safety))
(check-sat)
(get-model)
