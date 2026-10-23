; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun c22ee7710_alice_basis () Int)
(declare-fun c22ee7710_alice_market_value () Int)
(declare-fun c22ee7710_bob_basis () Int)
(declare-fun c22ee7710_bob_market_value () Int)
(declare-fun c22ee7710_collusion_occurs () Bool)
(declare-fun c22ee7710_fee_evasion_occurs () Bool)
(assert
 (= c22ee7710_alice_basis c22ee7710_alice_basis))
(assert
 (= c22ee7710_alice_market_value c22ee7710_alice_market_value))
(assert
 (= c22ee7710_bob_basis c22ee7710_bob_basis))
(assert
 (= c22ee7710_bob_market_value c22ee7710_bob_market_value))
(assert
 (= c22ee7710_collusion_occurs c22ee7710_collusion_occurs))
(assert
 (= c22ee7710_fee_evasion_occurs c22ee7710_fee_evasion_occurs))
(define-fun report_preconditions () Bool (and (> c22ee7710_alice_market_value c22ee7710_alice_basis)
     (> c22ee7710_bob_basis c22ee7710_bob_market_value)
     c22ee7710_collusion_occurs))
(define-fun report_safety () Bool (=> (and (> c22ee7710_alice_market_value c22ee7710_alice_basis)
         (> c22ee7710_bob_basis c22ee7710_bob_market_value)
         c22ee7710_collusion_occurs)
    (not c22ee7710_fee_evasion_occurs)))
(define-fun report_effects () Bool (and (> c22ee7710_alice_market_value c22ee7710_alice_basis)
     (> c22ee7710_bob_basis c22ee7710_bob_market_value)
     c22ee7710_collusion_occurs
     (not (not c22ee7710_fee_evasion_occurs))))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
