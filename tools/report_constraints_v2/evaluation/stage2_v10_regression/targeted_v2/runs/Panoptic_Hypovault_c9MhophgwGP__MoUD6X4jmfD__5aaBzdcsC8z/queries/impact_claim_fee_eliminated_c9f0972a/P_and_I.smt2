; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbb8a2b68_alice_basis () Int)
(declare-fun cbb8a2b68_alice_market_value () Int)
(declare-fun cbb8a2b68_bob_basis () Int)
(declare-fun cbb8a2b68_bob_market_value () Int)
(declare-fun cbb8a2b68_collusion_occurred () Bool)
(declare-fun cbb8a2b68_performance_fee_charged () Bool)
(assert
 (= cbb8a2b68_alice_basis cbb8a2b68_alice_basis))
(assert
 (= cbb8a2b68_alice_market_value cbb8a2b68_alice_market_value))
(assert
 (= cbb8a2b68_bob_basis cbb8a2b68_bob_basis))
(assert
 (= cbb8a2b68_bob_market_value cbb8a2b68_bob_market_value))
(assert
 (= cbb8a2b68_collusion_occurred cbb8a2b68_collusion_occurred))
(assert
 (= cbb8a2b68_performance_fee_charged cbb8a2b68_performance_fee_charged))
(define-fun report_preconditions () Bool (and (> cbb8a2b68_alice_market_value cbb8a2b68_alice_basis)
     (> cbb8a2b68_bob_basis cbb8a2b68_bob_market_value)
     cbb8a2b68_collusion_occurred))
(define-fun report_safety () Bool (=> (and (> cbb8a2b68_alice_market_value cbb8a2b68_alice_basis)
         cbb8a2b68_collusion_occurred)
    cbb8a2b68_performance_fee_charged))
(define-fun report_effects () Bool (and (> cbb8a2b68_alice_market_value cbb8a2b68_alice_basis)
     cbb8a2b68_collusion_occurred
     (not cbb8a2b68_performance_fee_charged)))
(assert report_preconditions)
(assert report_safety)
(check-sat)
(get-model)
