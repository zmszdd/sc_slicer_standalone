; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cb25aeb37_alice_cost_basis () Int)
(declare-fun cb25aeb37_alice_market_value () Int)
(declare-fun cb25aeb37_bob_cost_basis () Int)
(declare-fun cb25aeb37_bob_market_value () Int)
(declare-fun cb25aeb37_collusion_occurs () Bool)
(declare-fun cb25aeb37_loss_basis_market_created () Bool)
(assert
 (= cb25aeb37_alice_cost_basis cb25aeb37_alice_cost_basis))
(assert
 (= cb25aeb37_alice_market_value cb25aeb37_alice_market_value))
(assert
 (= cb25aeb37_bob_cost_basis cb25aeb37_bob_cost_basis))
(assert
 (= cb25aeb37_bob_market_value cb25aeb37_bob_market_value))
(assert
 (= cb25aeb37_collusion_occurs cb25aeb37_collusion_occurs))
(assert
 (= cb25aeb37_loss_basis_market_created cb25aeb37_loss_basis_market_created))
(define-fun report_preconditions () Bool (and (> cb25aeb37_alice_market_value cb25aeb37_alice_cost_basis)
     (> cb25aeb37_bob_cost_basis cb25aeb37_bob_market_value)
     cb25aeb37_collusion_occurs))
(define-fun report_safety () Bool (=> (and (> cb25aeb37_alice_market_value cb25aeb37_alice_cost_basis)
         (> cb25aeb37_bob_cost_basis cb25aeb37_bob_market_value)
         cb25aeb37_collusion_occurs)
    (not cb25aeb37_loss_basis_market_created)))
(define-fun report_effects () Bool (and (> cb25aeb37_alice_market_value cb25aeb37_alice_cost_basis)
     (> cb25aeb37_bob_cost_basis cb25aeb37_bob_market_value)
     cb25aeb37_collusion_occurs
     (not (not cb25aeb37_loss_basis_market_created))))
