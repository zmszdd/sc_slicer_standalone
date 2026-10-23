; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c10558c82_alice_basis () Int)
(declare-fun c10558c82_alice_market_value () Int)
(declare-fun c10558c82_bob_basis () Int)
(declare-fun c10558c82_bob_market_value () Int)
(declare-fun c10558c82_fee_charged () Bool)
(assert
 (= c10558c82_alice_basis c10558c82_alice_basis))
(assert
 (= c10558c82_alice_market_value c10558c82_alice_market_value))
(assert
 (= c10558c82_bob_basis c10558c82_bob_basis))
(assert
 (= c10558c82_bob_market_value c10558c82_bob_market_value))
(assert
 (= c10558c82_fee_charged c10558c82_fee_charged))
(define-fun report_preconditions () Bool (and (> c10558c82_alice_market_value c10558c82_alice_basis)
     (> c10558c82_bob_basis c10558c82_bob_market_value)))
(define-fun report_safety () Bool (=> (and (> c10558c82_alice_market_value c10558c82_alice_basis)
         (> c10558c82_bob_basis c10558c82_bob_market_value))
    c10558c82_fee_charged))
(define-fun report_effects () Bool (and (> c10558c82_alice_market_value c10558c82_alice_basis)
     (> c10558c82_bob_basis c10558c82_bob_market_value)
     (not c10558c82_fee_charged)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
