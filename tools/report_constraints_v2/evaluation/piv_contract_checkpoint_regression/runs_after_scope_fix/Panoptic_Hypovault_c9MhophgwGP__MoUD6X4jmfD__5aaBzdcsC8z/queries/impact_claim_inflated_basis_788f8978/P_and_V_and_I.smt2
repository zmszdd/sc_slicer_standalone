; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c7d786a7b_alice_basis_after_merge () Int)
(declare-fun c7d786a7b_alice_cost_basis () Int)
(declare-fun c7d786a7b_alice_market_value () Int)
(declare-fun c7d786a7b_alice_market_value_after_merge () Int)
(declare-fun c7d786a7b_bob_cost_basis () Int)
(declare-fun c7d786a7b_bob_market_value () Int)
(declare-fun c7d786a7b_collusion_occurs () Bool)
(assert
 (= c7d786a7b_alice_basis_after_merge c7d786a7b_alice_basis_after_merge))
(assert
 (= c7d786a7b_alice_cost_basis c7d786a7b_alice_cost_basis))
(assert
 (= c7d786a7b_alice_market_value c7d786a7b_alice_market_value))
(assert
 (= c7d786a7b_alice_market_value_after_merge c7d786a7b_alice_market_value_after_merge))
(assert
 (= c7d786a7b_bob_cost_basis c7d786a7b_bob_cost_basis))
(assert
 (= c7d786a7b_bob_market_value c7d786a7b_bob_market_value))
(assert
 (= c7d786a7b_collusion_occurs c7d786a7b_collusion_occurs))
(define-fun report_preconditions () Bool (and (> c7d786a7b_alice_market_value c7d786a7b_alice_cost_basis)
     (> c7d786a7b_bob_cost_basis c7d786a7b_bob_market_value)
     c7d786a7b_collusion_occurs))
(define-fun report_safety () Bool (=> (and (> c7d786a7b_alice_market_value c7d786a7b_alice_cost_basis)
         (> c7d786a7b_bob_cost_basis c7d786a7b_bob_market_value)
         c7d786a7b_collusion_occurs)
    (< c7d786a7b_alice_basis_after_merge
       c7d786a7b_alice_market_value_after_merge)))
(define-fun report_effects () Bool (and (> c7d786a7b_alice_market_value c7d786a7b_alice_cost_basis)
     (> c7d786a7b_bob_cost_basis c7d786a7b_bob_market_value)
     c7d786a7b_collusion_occurs
     (not (< c7d786a7b_alice_basis_after_merge
             c7d786a7b_alice_market_value_after_merge))))
(assert report_preconditions)
(assert report_effects)
(assert report_safety)
(check-sat)
