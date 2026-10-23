; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cbb8a2b68_alice_bob_collude () Bool)
(declare-fun cbb8a2b68_alice_market_value_exceeds_basis () Bool)
(declare-fun cbb8a2b68_bob_position_at_loss () Bool)
(declare-fun cbb8a2b68_performance_fee_charged () Bool)
(assert
 (= cbb8a2b68_alice_bob_collude cbb8a2b68_alice_bob_collude))
(assert
 (= cbb8a2b68_alice_market_value_exceeds_basis cbb8a2b68_alice_market_value_exceeds_basis))
(assert
 (= cbb8a2b68_bob_position_at_loss cbb8a2b68_bob_position_at_loss))
(assert
 (= cbb8a2b68_performance_fee_charged cbb8a2b68_performance_fee_charged))
(define-fun report_preconditions () Bool (and cbb8a2b68_alice_market_value_exceeds_basis
     cbb8a2b68_bob_position_at_loss
     cbb8a2b68_alice_bob_collude))
(define-fun report_safety () Bool (=> (and cbb8a2b68_alice_market_value_exceeds_basis
         cbb8a2b68_bob_position_at_loss
         cbb8a2b68_alice_bob_collude)
    cbb8a2b68_performance_fee_charged))
(define-fun report_effects () Bool (and cbb8a2b68_alice_market_value_exceeds_basis
     cbb8a2b68_bob_position_at_loss
     cbb8a2b68_alice_bob_collude
     (not cbb8a2b68_performance_fee_charged)))
(assert report_preconditions)
(assert report_effects)
(check-sat)
(get-model)
